import asyncio
import MetaTrader5 as Mt
import requests as requests


class DealComment:
    # comment = {
    #     'lieder_ticket': -1,
    #     'reason': '',  # Закрыто лидером, Закрыто по условию стоп-лосс
    # }

    lieder_ticket: int
    reason: str
    SEPARATOR = ':'

    def __init__(self):
        self.lieder_ticket = -1
        self.reason = ''

    @staticmethod
    def is_valid_string(string: str):
        if len(string) > 0:
            sliced = string.split(DealComment.SEPARATOR)
            if len(sliced) == 2:
                # if sliced[1] not in reasons_code:
                #     return False
                try:
                    ticket = int(sliced[0])
                    if ticket < 0:
                        return False
                except ValueError:
                    return False
            else:
                return False
        return True

    def string(self):
        return f'{self.lieder_ticket}' + DealComment.SEPARATOR + f'{self.reason}'

    def obj(self):
        return {'lieder_ticket': self.lieder_ticket, 'reason': self.reason}

    def set_from_string(self, string: str):
        if DealComment.SEPARATOR in string:
            split_str = string.split(DealComment.SEPARATOR)
            lid_str = split_str[0]
            cause = split_str[1]
        elif len(string) > 0:
            lid_str = string
            cause = ''
        else:
            lid_str = '-1'
            cause = ''
        try:
            self.lieder_ticket = int(lid_str)
            self.reason = cause
        except ValueError:
            self.lieder_ticket = -1
            self.reason = ''
        return self

    def set_from_ticket(self, ticket: int):
        self.lieder_ticket = ticket
        self.reason = ''


TIMEOUT_INIT = 60_000  # время ожидания при инициализации терминала (рекомендуемое 60_000 millisecond)
MAGIC = 9876543210  # идентификатор эксперта
DEVIATION = 20  # допустимое отклонение цены в пунктах при совершении сделки

source = {
    # 'lieder': {},
    # 'investors': [{}, {}],
    # 'settings': {}
}
signals_settings = {}
signal = {}
signal_event = asyncio.Event()  # init async event

sleep_update = 10  # пауза

host = 'http://127.0.0.1:8000/api/'


def set_dummy_data():
    investment_size = 1000
    source['lieder'] = {
        'terminal_path': r'C:\Program Files\MetaTrader 5\terminal64.exe',
        'login': 66587203,
        'password': '3hksvtko',
        'server': 'MetaQuotes-Demo'
    }
    source['investors'] = [
        {
            'terminal_path': r'C:\Program Files\MetaTrader 5_2\terminal64.exe',
            'login': 65766034,
            'password': 'h0nmgczo',
            'server': 'MetaQuotes-Demo',
            'investment_size': investment_size,
            'dcs_access': True,

            'deal_in_plus': 0.1,
            'deal_in_minus': -0.1,
            'waiting_time': 1,
            'ask_an_investor': 'Все',
            'price_refund': 'Да',
            # -----------------------------------------
            'multiplier': 'Баланс',
            'multiplier_value': 100.0,
            'changing_multiplier': 'Да',
            # -----------------------------------------
            'stop_loss': 'Процент',
            'stop_value': 20.0,
            'open_trades': 'Закрыть',
            # -----------------------------------------
            'shutdown_initiator': 'Инвестор',
            'disconnect': 'Нет',
            'open_trades_disconnect': 'Закрыть',
            'notification': 'Нет',
            'blacklist': 'Нет',
            'accompany_transactions': 'Нет',
            # -----------------------------------------=
            'no_exchange_connection': 'Нет',
            'api_key_expired': 'Нет',
            # -----------------------------------------
            'closed_deals_myself': 'Переоткрывать',
            'reconnected': 'Переоткрывать',
            # -----------------------------------------
            'recovery_model': 'Не корректировать',
            'buy_hold_model': 'Не корректировать',
            # -----------------------------------------
            'not_enough_margin': 'Минимальный объем',
            'accounts_in_diff_curr': 'Доллары',
            # -----------------------------------------
            'synchronize_deals': 'Нет',
            'deals_not_opened': 'Нет',
            'closed_deal_investor': 'Нет',
            # -----------------------------------------
        }
    ]
    source['investors'].append(source['investors'][0].copy())
    source['investors'][1]['terminal_path'] = r'C:\Program Files\MetaTrader 5_3\terminal64.exe'
    source['investors'][1]['login'] = 5009600048
    source['investors'][1]['password'] = 'sbbsapv5'


def init_mt(init_data):
    """Инициализация терминала"""
    return Mt.initialize(login=init_data['login'], server=init_data['server'], password=init_data['password'],
                         path=init_data['terminal_path'], timeout=TIMEOUT_INIT)


async def open_position(symbol, deal_type, lot, sender_ticket: int, tp=0.0, sl=0.0):
    """Открытие позиции"""
    try:
        point = Mt.symbol_info(symbol).point
        price = tp_in = sl_in = 0.0
        if deal_type == 0:  # BUY
            deal_type = Mt.ORDER_TYPE_BUY
            price = Mt.symbol_info_tick(symbol).ask
        if tp != 0:
            tp_in = price + tp * point
        if sl != 0:
            sl_in = price - sl * point
        elif deal_type == 1:  # SELL
            deal_type = Mt.ORDER_TYPE_SELL
            price = Mt.symbol_info_tick(symbol).bid
            if tp != 0:
                tp_in = price - tp * point
            if sl != 0:
                sl_in = price + sl * point
    except AttributeError:
        return {'retcode': -200}
    comment = DealComment()
    comment.lieder_ticket = sender_ticket
    comment.reason = '01'
    request = {
        "action": Mt.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": deal_type,
        "price": price,
        "sl": sl_in,
        "tp": tp_in,
        "deviation": DEVIATION,
        "magic": MAGIC,
        "comment": comment.string(),
        "type_time": Mt.ORDER_TIME_GTC,
        "type_filling": Mt.ORDER_FILLING_FOK,
    }
    result = Mt.order_send(request)
    return result


def is_signal_actual(signal_item, deviation_actual):
    price = signal_item['open_price']
    prc = price / 100
    top = price + deviation_actual * prc
    bottom = price - deviation_actual * prc
    return bottom < price < top


async def get_settings(sleep=sleep_update):
    global signals_settings
    url = host + 'signals_settings'
    while True:
        response = requests.get(url)
        if response.status_code == 200:
            signals_settings = response.json()[0]
        await asyncio.sleep(sleep)


async def get_signal(sleep=sleep_update):
    global signals_settings, signal
    url = host + 'all_signals'
    while True:
        if len(signals_settings) > 0:
            response = requests.get(url)
            if response.status_code == 200:
                signal = response.json()[0]
                signal_event.set()
            else:
                signal = {}
            await asyncio.sleep(sleep)


async def task_manager():
    while True:
        await signal_event.wait()
        event_loop.create_task(execute_signal())
        signal.clear()


async def execute_signal():
    if is_signal_actual(signal, signals_settings['signal_relevance']):
        await open_position(symbol=signal['signal_symbol'], deal_type=signal['deal_type'], lot=signal['deal_lot'],
                            sender_ticket=signal['ticket'])


if __name__ == '__main__':
    event_loop = asyncio.new_event_loop()
    event_loop.create_task(get_settings())
    event_loop.create_task(get_signal())
    event_loop.create_task(task_manager())
    event_loop.run_forever()
