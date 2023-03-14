import asyncio
import aiohttp
from datetime import datetime, timedelta
from math import fabs
import MetaTrader5 as Mt

send_retcodes = {
    -800: ('CUSTOM_RETCODE_NOT_ENOUGH_MARGIN', 'Уменьшите множитель или увеличьте сумму инвестиции'),
    -700: ('CUSTOM_RETCODE_LIMITS_NOT_CHANGED', 'Уровни не изменены'),
    -600: ('CUSTOM_RETCODE_POSITION_NOT_MODIFIED', 'Объем сделки не изменен'),
    -500: ('CUSTOM_RETCODE_POSITION_NOT_MODIFIED', 'Объем сделки не изменен'),
    -400: ('CUSTOM_RETCODE_POSITION_NOT_MODIFIED', 'Объем сделки не изменен'),
    -300: ('CUSTOM_RETCODE_EQUAL_VOLUME', 'Новый объем сделки равен существующему'),
    -200: ('CUSTOM_RETCODE_WRONG_SYMBOL', 'Нет такого торгового символа'),
    -100: ('CUSTOM_RETCODE_NOT_ENOUGH_MARGIN', 'Нехватка маржи. Выбран режим - Не открывать сделку или Не выбрано'),
    10004: ('TRADE_RETCODE_REQUOTE', 'Реквота'),
    10006: ('TRADE_RETCODE_REJECT', 'Запрос отклонен'),
    10007: ('TRADE_RETCODE_CANCEL', 'Запрос отменен трейдером'),
    10008: ('TRADE_RETCODE_PLACED', 'Ордер размещен'),
    10009: ('TRADE_RETCODE_DONE', 'Заявка выполнена'),
    10010: ('TRADE_RETCODE_DONE_PARTIAL', 'Заявка выполнена частично'),
    10011: ('TRADE_RETCODE_ERROR', 'Ошибка обработки запроса'),
    10012: ('TRADE_RETCODE_TIMEOUT', 'Запрос отменен по истечению времени'),
    10013: ('TRADE_RETCODE_INVALID', 'Неправильный запрос'),
    10014: ('TRADE_RETCODE_INVALID_VOLUME', 'Неправильный объем в запросе'),
    10015: ('TRADE_RETCODE_INVALID_PRICE', 'Неправильная цена в запросе'),
    10016: ('TRADE_RETCODE_INVALID_STOPS', 'Неправильные стопы в запросе'),
    10017: ('TRADE_RETCODE_TRADE_DISABLED', 'Торговля запрещена'),
    10018: ('TRADE_RETCODE_MARKET_CLOSED', 'Рынок закрыт'),
    10019: ('TRADE_RETCODE_NO_MONEY', 'Нет достаточных денежных средств для выполнения запроса'),
    10020: ('TRADE_RETCODE_PRICE_CHANGED', 'Цены изменились'),
    10021: ('TRADE_RETCODE_PRICE_OFF', 'Отсутствуют котировки для обработки запроса'),
    10022: ('TRADE_RETCODE_INVALID_EXPIRATION', 'Неверная дата истечения ордера в запросе'),
    10023: ('TRADE_RETCODE_ORDER_CHANGED', 'Состояние ордера изменилось'),
    10024: ('TRADE_RETCODE_TOO_MANY_REQUESTS', 'Слишком частые запросы'),
    10025: ('TRADE_RETCODE_NO_CHANGES', 'В запросе нет изменений'),
    10026: ('TRADE_RETCODE_SERVER_DISABLES_AT', 'Автотрейдинг запрещен сервером'),
    10027: ('TRADE_RETCODE_CLIENT_DISABLES_AT', 'Автотрейдинг запрещен клиентским терминалом'),
    10028: ('TRADE_RETCODE_LOCKED', 'Запрос заблокирован для обработки'),
    10029: ('TRADE_RETCODE_FROZEN', 'Ордер или позиция заморожены'),
    10030: ('TRADE_RETCODE_INVALID_FILL', 'Указан неподдерживаемый тип исполнения ордера по остатку'),
    10031: ('TRADE_RETCODE_CONNECTION', 'Нет соединения с торговым сервером'),
    10032: ('TRADE_RETCODE_ONLY_REAL', 'Операция разрешена только для реальных счетов'),
    10033: ('TRADE_RETCODE_LIMIT_ORDERS', 'Достигнут лимит на количество отложенных ордеров'),
    10034: (
        'TRADE_RETCODE_LIMIT_VOLUME', 'Достигнут лимит на объем ордеров и позиций для данного символа'),
    10035: ('TRADE_RETCODE_INVALID_ORDER', 'Неверный или запрещённый тип ордера'),
    10036: ('TRADE_RETCODE_POSITION_CLOSED', 'Позиция с указанным POSITION_IDENTIFIER уже закрыта'),
    10038: ('TRADE_RETCODE_INVALID_CLOSE_VOLUME', 'Закрываемый объем превышает текущий объем позиции'),
    10039: ('TRADE_RETCODE_CLOSE_ORDER_EXIST', 'Для указанной позиции уже есть ордер на закрытие'),
    10040: ('TRADE_RETCODE_LIMIT_POSITIONS',
            'Количество открытых позиций, которое можно одновременно иметь на счете, '
            'может быть ограничено настройками сервера'),
    10041: (
        'TRADE_RETCODE_REJECT_CANCEL',
        'Запрос на активацию отложенного ордера отклонен, а сам ордер отменен'),
    10042: (
        'TRADE_RETCODE_LONG_ONLY',
        'Запрос отклонен, так как на символе установлено правило "Разрешены только '
        'длинные позиции"  (POSITION_TYPE_BUY)'),
    10043: ('TRADE_RETCODE_SHORT_ONLY',
            'Запрос отклонен, так как на символе установлено правило "Разрешены только '
            'короткие позиции" (POSITION_TYPE_SELL)'),
    10044: ('TRADE_RETCODE_CLOSE_ONLY',
            'Запрос отклонен, так как на символе установлено правило "Разрешено только '
            'закрывать существующие позиции"'),
    10045: ('TRADE_RETCODE_FIFO_CLOSE',
            'Запрос отклонен, так как для торгового счета установлено правило "Разрешено '
            'закрывать существующие позиции только по правилу FIFO" ('
            'ACCOUNT_FIFO_CLOSE=true)'),
    10046: (
        'TRADE_RETCODE_HEDGE_PROHIBITED',
        'Запрос отклонен, так как для торгового счета установлено правило '
        '"Запрещено открывать встречные позиции по одному символу"')}
last_errors = {
    1: ('RES_S_OK', 'generic success'),
    -1: ('RES_E_FAIL', 'generic fail'),
    -2: ('RES_E_INVALID_PARAMS', 'invalid arguments/parameters'),
    -3: ('RES_E_NO_MEMORY', 'no memory condition'),
    -4: ('RES_E_NOT_FOUND', 'no history'),
    -5: ('RES_E_INVALID_VERSION', 'invalid version'),
    -6: ('RES_E_AUTH_FAILED', 'authorization failed'),
    -7: ('RES_E_UNSUPPORTED', 'unsupported method'),
    -8: ('RES_E_AUTO_TRADING_DISABLED', 'auto-trading disabled'),
    -10000: ('RES_E_INTERNAL_FAIL', 'internal IPC general error'),
    -10001: ('RES_E_INTERNAL_FAIL_SEND', 'internal IPC send failed'),
    -10002: ('RES_E_INTERNAL_FAIL_RECEIVE', 'internal IPC recv failed'),
    -10003: ('RES_E_INTERNAL_FAIL_INIT', 'internal IPC initialization fail'),
    -10003: ('RES_E_INTERNAL_FAIL_CONNECT', 'internal IPC no ipc'),
    -10005: ('RES_E_INTERNAL_FAIL_TIMEOUT', 'internal timeout')}
reasons_code = {
    '01': 'Открыто СКС',
    '02': 'Блеклист',
    '03': 'Закрыто по команде пользователя',
    '04': 'Ключ APi истек',
    '05': 'Нет связи с биржей',
    '06': 'Закрыто инвестором',
    '07': 'Закрыто по условию стоп-лосс',
    '08': 'Объем изменен',
    '09': 'Лимиты изменены',
}


class DealComment:
    # comment = {
    #     'lieder_ticket': -1,
    #     'reason': '',  # Закрыто лидером, Закрыто по условию стоп-лосс
    # }

    lieder_ticket: int
    reason: str
    SEPARATOR = '-'

    def __init__(self):
        self.lieder_ticket = -1
        self.reason = ''

    @staticmethod
    def is_valid_string(string: str):
        if len(string) > 0:
            sliced = string.split(DealComment.SEPARATOR)
            if len(sliced) == 2:
                if sliced[1] not in reasons_code:
                    return False
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
lieder_positions = []  # default var
signals_settings = {}
SERVER_DELTA_TIME = timedelta(hours=4)
start_date = datetime.now().replace(microsecond=0)
trading_event = asyncio.Event()  # init async event

sleep_update = 3  # пауза для обновления лидера

host = 'http://127.0.0.1:8000/api/'

source = {
    # 'lieder': {},
    # 'investors': [{}, {}],
    # 'settings': {}
}


def set_dummy_data():
    global start_date
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
    source['settings'] = {
        "relevance": True,
        "update_at": str(start_date),
        "create_at": str(start_date)
        # "access": response['access'],
    }


def init_mt(init_data):
    """Инициализация терминала"""
    res = Mt.initialize(login=init_data['login'], server=init_data['server'], password=init_data['password'],
                        path=init_data['terminal_path'], timeout=TIMEOUT_INIT, port=8223)
    return res


def get_pos_pips_tp(position, price=None):
    """Расчет Тейк-профит в пунктах"""
    if price is None:
        price = position.price_open
    result = 0.0
    if position.tp > 0:
        result = round(fabs(price - position.tp) / Mt.symbol_info(position.symbol).point)
    return result


def get_pos_pips_sl(position, price=None):
    """Расчет Стоп-лосс в пунктах"""
    if price is None:
        price = position.price_open
    result = 0.0
    if position.sl > 0:
        result = round(fabs(price - position.sl) / Mt.symbol_info(position.symbol).point)
    return result


def get_investor_positions(only_own=True):
    """Количество открытых позиций"""
    result = []
    if len(source) > 0:
        positions = Mt.positions_get()
        if not positions:
            positions = []
        if only_own and len(positions) > 0:
            for _ in positions:
                if positions[positions.index(_)].magic == MAGIC and DealComment.is_valid_string(_.comment):
                    result.append(_)
        else:
            result = positions
    return result


def is_position_opened(lieder_position, investor):
    """Проверка позиции лидера на наличие в списке позиций и истории инвестора"""
    init_mt(init_data=investor)
    invest_positions = get_investor_positions(only_own=False)
    if len(invest_positions) > 0:
        for pos in invest_positions:
            if DealComment.is_valid_string(pos.comment):
                comment = DealComment().set_from_string(pos.comment)
                if lieder_position.ticket == comment.lieder_ticket:
                    return True
    return False


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


def close_position(investor, position, reason):
    """Закрытие указанной позиции"""
    init_mt(init_data=investor)
    tick = Mt.symbol_info_tick(position.symbol)
    if not tick:
        return
    new_comment_str = position.comment
    if DealComment.is_valid_string(position.comment):
        comment = DealComment().set_from_string(position.comment)
        comment.reason = reason
        new_comment_str = comment.string()
    request = {
        'action': Mt.TRADE_ACTION_DEAL,
        'position': position.ticket,
        'symbol': position.symbol,
        'volume': position.volume,
        'type': Mt.ORDER_TYPE_BUY if position.type == 1 else Mt.ORDER_TYPE_SELL,
        'price': tick.ask if position.type == 1 else tick.bid,
        'deviation': DEVIATION,
        'magic:': MAGIC,
        'comment': new_comment_str,
        'type_tim': Mt.ORDER_TIME_GTC,
        'type_filing': Mt.ORDER_FILLING_IOC
    }
    result = Mt.order_send(request)
    # print(result)
    return result


def force_close_all_positions(investor, reason):
    """Принудительное закрытие всех позиций аккаунта"""
    init_res = init_mt(init_data=investor)
    if init_res:
        positions = get_investor_positions(only_own=False)
        if len(positions) > 0:
            for position in positions:
                if position.magic == MAGIC and DealComment.is_valid_string(position.comment):
                    close_position(investor, position, reason=reason)
        # Mt.shutdown()


def close_positions_by_lieder(investor):
    """Закрытие позиций инвестора, которые закрылись у лидера"""
    init_mt(init_data=investor)
    positions_investor = get_investor_positions()
    non_existed_positions = []
    if positions_investor:
        for ip in positions_investor:
            position_exist = False
            for lp in lieder_positions:
                comment = DealComment().set_from_string(ip.comment)
                if comment.lieder_ticket == lp.ticket:
                    position_exist = True
                    break
            if not position_exist:
                non_existed_positions.append(ip)
    for pos in non_existed_positions:
        print('     close position:', pos.comment)
        close_position(investor, pos, reason='06')


async def get_settings(sleep=sleep_update):
    global signals_settings
    url = host + 'signals_settings'
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as get_response:
                    response = await get_response.json()
        except Exception as e:
            print(e)
            response = {}
        signals_settings = response
        await asyncio.sleep(sleep)


async def update_lieder_info(sleep=sleep_update):
    global lieder_positions, source
    while True:
        if len(source) > 0:
            init_res = init_mt(init_data=source['lieder'])
            if not init_res:
                await asyncio.sleep(sleep)
                continue
            lieder_positions = Mt.positions_get()
            print(
                f'\nLIEDER {source["lieder"]["login"]} [{source["lieder"]["currency"]}] - {len(lieder_positions)} positions :',
                datetime.utcnow().replace(microsecond=0))
            trading_event.set()
        await asyncio.sleep(sleep)


async def execute_investor(investor):
    return

    init_res = init_mt(init_data=investor)
    if not init_res:
        # await set_comment('Ошибка инициализации инвестора ' + str(investor['login']))
        return
    # print(f' - {investor["login"]} [{investor["currency"]}] - {len(Mt.positions_get())} positions. Access:',
    #       investor['dcs_access'])  # , end='')
    # enable_algotrading()

    # for _ in get_investor_positions():
    #     print('\n', Mt.symbol_info(_.symbol).path)
    # print(Mt.symbol_info('EURUSD').margin_initial)

    if investor['dcs_access']:

        for pos_lid in lieder_positions:
            inv_tp = get_pos_pips_tp(pos_lid)
            inv_sl = get_pos_pips_sl(pos_lid)
            init_mt(investor)
            if not is_position_opened(pos_lid, investor):
                ret_code = None
                volume = 1.0

                # min_lot = Mt.symbol_info(pos_lid.symbol).volume_min
                # decimals = str(min_lot)[::-1].find('.')
                response = await open_position(symbol=pos_lid.symbol, deal_type=pos_lid.type,
                                               lot=volume, sender_ticket=pos_lid.ticket,
                                               tp=inv_tp, sl=inv_sl)
                if response:
                    try:
                        ret_code = response.retcode
                    except AttributeError:
                        ret_code = response['retcode']
                if ret_code:
                    msg = str(investor['login']) + ' ' + send_retcodes[ret_code][1]  # + ' : ' + str(ret_code)
                    # if ret_code != 10009:  # Заявка выполнена
                    # await set_comment('\t' + msg)
                    print(msg)

    # закрытие позиций от лидера
    if True:
        close_positions_by_lieder(investor)

    # Mt.shutdown()


async def task_manager():
    while True:
        await trading_event.wait()

        if len(source) > 0:
            for _ in source['investors']:
                event_loop.create_task(execute_investor(_))

        trading_event.clear()


if __name__ == '__main__':
    # set_dummy_data()
    event_loop = asyncio.new_event_loop()
    # event_loop.create_task(update_setup())  # для теста без сервера закомментировать
    event_loop.create_task(get_settings())

    # event_loop.create_task(update_lieder_info())
    # event_loop.create_task(task_manager())
    event_loop.run_forever()
