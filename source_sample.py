import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from math import fabs
import MetaTrader5 as Mt
import requests

send_retcodes = {
    -200: ('CUSTOM_RETCODE_WRONG_SYMBOL', 'Нет такого торгового символа'),
    -100: ('CUSTOM_RETCODE_NOT_ENOUGH_MARGIN', 'Нехватка маржи. Выбран режим - Не открывать сделку'),
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
    10034: ('TRADE_RETCODE_LIMIT_VOLUME', 'Достигнут лимит на объем ордеров и позиций для данного символа'),
    10035: ('TRADE_RETCODE_INVALID_ORDER', 'Неверный или запрещённый тип ордера'),
    10036: ('TRADE_RETCODE_POSITION_CLOSED', 'Позиция с указанным POSITION_IDENTIFIER уже закрыта'),
    10038: ('TRADE_RETCODE_INVALID_CLOSE_VOLUME', 'Закрываемый объем превышает текущий объем позиции'),
    10039: ('TRADE_RETCODE_CLOSE_ORDER_EXIST', 'Для указанной позиции уже есть ордер на закрытие'),
    10040: ('TRADE_RETCODE_LIMIT_POSITIONS', 'Количество открытых позиций, которое можно одновременно иметь на счете, '
                                             'может быть ограничено настройками сервера'),
    10041: ('TRADE_RETCODE_REJECT_CANCEL', 'Запрос на активацию отложенного ордера отклонен, а сам ордер отменен'),
    10042: ('TRADE_RETCODE_LONG_ONLY', 'Запрос отклонен, так как на символе установлено правило "Разрешены только '
                                       'длинные позиции"  (POSITION_TYPE_BUY)'),
    10043: ('TRADE_RETCODE_SHORT_ONLY', 'Запрос отклонен, так как на символе установлено правило "Разрешены только '
                                        'короткие позиции" (POSITION_TYPE_SELL)'),
    10044: ('TRADE_RETCODE_CLOSE_ONLY', 'Запрос отклонен, так как на символе установлено правило "Разрешено только '
                                        'закрывать существующие позиции"'),
    10045: ('TRADE_RETCODE_FIFO_CLOSE', 'Запрос отклонен, так как для торгового счета установлено правило "Разрешено '
                                        'закрывать существующие позиции только по правилу FIFO" ('
                                        'ACCOUNT_FIFO_CLOSE=true)'),
    10046: ('TRADE_RETCODE_HEDGE_PROHIBITED', 'Запрос отклонен, так как для торгового счета установлено правило '
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


class DealComment:
    # comment = {
    #     'lieder_ticket': -1,
    #     'reason': '',  # Закрыто лидером, Закрыто по условию стоп-лосс
    # }

    lieder_ticket: int
    reason: str

    # def __init__(self, ticket: int, reason: str):
    #     if reason is None or ticket is None:
    #         self.lieder_ticket = -1
    #         self.reason = ''
    #     else:
    #         self.lieder_ticket = ticket
    #         self.reason = reason

    def __init__(self):
        self.lieder_ticket = -1
        self.reason = ''

    @staticmethod
    def is_valid_string(string: str):
        if len(string) > 0:
            sliced = string.split('|')
            if len(sliced) == 2:
                try:
                    ticket = int(sliced[0])
                    if ticket < 0:
                        return False
                except ValueError:
                    return False
        return True

    def string(self):
        return f'{self.lieder_ticket}|{self.reason}'

    def obj(self):
        return {'lieder_ticket': self.lieder_ticket, 'reason': self.reason}

    def set_from_string(self, string: str):
        if '|' in string:
            split_str = string.split('|')
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


TIMEOUT_INIT = 10_000  # время ожидания при инициализации терминала (рекомендуемое 60_000 millisecond)
MAGIC = 9876543210  # идентификатор эксперта
DEVIATION = 20  # допустимое отклонение цены в пунктах при совершении сделки
UTC_OFFSET_TIMEDELTA = datetime.now() - datetime.utcnow()

output_report = []  # сюда выводится отчет
lieder_balance = 0  # default var
lieder_equity = 0  # default var
lieder_positions = []  # default var
listed_signals = []  # default var
investor_positions = {}  # default var
old_investors_balance = []
start_date = datetime.now().replace(microsecond=0) + UTC_OFFSET_TIMEDELTA  # default var
trading_event = asyncio.Event()  # init async event

sleep_lieder_update = 10  # пауза для обновления лидера
send_messages = True  # отправлять сообщения в базу

host = 'https://my.atimex.io:8000/api/demo_mt5/'

source = {
    # 'lieder': {},
    # 'investors': [{}, {}],
    # 'settings': {}
}


# def enable_algotrading():
#     """Принудительное включение режима Аготрейдинга на терминале"""
#     try:
#         if not Mt.terminal_info().trade_allowed:
#             mt_wmcmd_experts = 32851
#             wm_command = 0x0111
#             ga_root = 2
#             terminal_handle = FindWindow('MetaQuotes::MetaTrader::5.00', None)
#             PostMessage(GetAncestor(terminal_handle, ga_root), wm_command, mt_wmcmd_experts, 0)
#     except AttributeError:
#         print(f'Невозможно подключиться к терминалу : {datetime.now()}')
#         exit()


def set_dummy_data():
    global send_messages, start_date
    send_messages = False
    investment_size = 1000
    source['lieder'] = {
        'terminal_path': r'C:\Program Files\MetaTrader 5\terminal64.exe',
        'login': 66727959,
        'password': 'o0oxqfke',
        'server': 'MetaQuotes-Demo'
    }
    source['investors'] = [
        {
            'terminal_path': r'C:\Program Files\MetaTrader 5_2\terminal64.exe',
            'login': 5010582378,
            'password': 'ykwp2tlw',
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
    # source['investors'][1]['terminal_path'] = r'C:\Program Files\MetaTrader 5_3\terminal64.exe'
    # source['investors'][1]['login'] = 5009600048
    # source['investors'][1]['password'] = 'sbbsapv5'
    source['settings'] = {
        "relevance": True,
        "update_at": str(start_date),
        "create_at": str(start_date)
        # "access": response['access'],
    }


def is_disconnect_changed(investor):
    if investor['disconnect_previous'] != investor['disconnect']:
        investor['disconnect_previous'] = investor['disconnect']
        return True
    return False


def disable_dcs(investors_list, investor):
    investor['dcs_access'] = False
    if send_messages:
        return
    investor_id = -1
    for _ in investors_list:
        if _['login'] == investor['login']:
            investor_id = investors_list.index(_)
            break
    if investor_id < 0:
        return
    id_shift = '_' + str(investor_id)
    url = host + 'list'
    response = requests.get(url).json()
    numb = response[-1]['id']
    url = host + f'patch/{numb}/'
    name = "access" + id_shift
    requests.patch(url=url, data={name: False})


def set_comment(comment):
    if not send_messages:
        return
    url = host + 'list'
    response = requests.get(url).json()
    numb = response[-1]['id']
    url = host + f'patch/{numb}/'
    # print('   ---   ', comment)
    requests.patch(url=url, data={"comment": comment})


def execute_conditions(investor):
    if investor['disconnect'] == 'Да' and is_disconnect_changed(investor):  # если отключился
        set_comment('Инициатор отключения: ' + investor['shutdown_initiator'])

    if investor['blacklist'] == 'Да':  # если в блек листе
        force_close_all_positions(investor, reason='Блеклист')
        disable_dcs(source['investors'], investor)
    if investor['disconnect'] == 'Да':  # если отключиться
        if get_investors_positions_count(investor) == 0:  # если нет открыты сделок
            disable_dcs(source['investors'], investor)

        if investor['open_trades_disconnect'] == 'Закрыть':  # если сделки закрыть
            force_close_all_positions(investor, 'Закрыто по команде пользователя')
            disable_dcs(source['investors'], investor)

        elif investor['accompany_transactions'] == 'Нет':  # если сделки оставить и не сопровождать
            disable_dcs(source['investors'], investor)


def init_mt(init_data, need_login=False):
    """Инициализация терминала"""
    if Mt.initialize(login=init_data['login'], server=init_data['server'], password=init_data['password'],
                     path=init_data['terminal_path'], timeout=TIMEOUT_INIT):
        # print(f'INVESTOR account {init_data["login"]} : {datetime.now()}')
        if need_login:
            if not Mt.login(login=init_data['login'], server=init_data['server'], password=init_data['password']):
                print('Login ERROR', Mt.last_error())
    else:
        print(f'>>>>> account {init_data["login"]} : {datetime.now()} : ERROR', Mt.last_error(),
              f': timeout = {TIMEOUT_INIT}')
        return False
        # exit()
    return True


def get_pips_tp(position, price=None):
    """Расчет Тейк-профит в пунктах"""
    if price is None:
        price = position.price_open
    result = 0.0
    if position.tp > 0:
        result = round(fabs(price - position.tp) / Mt.symbol_info(position.symbol).point)
    return result


def get_pips_sl(position, price=None):
    """Расчет Стоп-лосс в пунктах"""
    if price is None:
        price = position.price_open
    result = 0.0
    if position.sl > 0:
        result = round(fabs(price - position.sl) / Mt.symbol_info(position.symbol).point)
    return result


def get_investors_positions_count(investor):
    """Количество открытых позиций"""
    init_res = init_mt(init_data=investor)
    return Mt.positions_total() if init_res else -1


def is_position_exist_in_list(lieder_position, investor_positions):
    if len(investor_positions) <= 0:
        return False
    for pos in investor_positions:
        if DealComment.is_valid_string(pos.comment):
            comment = DealComment().set_from_string(pos.comment)
            if lieder_position.ticket == comment.lieder_ticket:
                return True
    return False


def is_position_exist_in_history(lieder_position):
    date_from = start_date  # datetime(2023, 2, 18, 1, 10)
    date_to = datetime.today().replace(microsecond=0) + UTC_OFFSET_TIMEDELTA
    history_deals = Mt.history_deals_get(date_from, date_to)

    # print('--', date_from, '-', lieder_position.ticket)
    # for _ in history_deals:
    #     print(history_deals.index(_), datetime.fromtimestamp(_.time), _.comment)

    if len(history_deals) > 0:
        for pos in history_deals:
            if pos.magic == MAGIC and DealComment.is_valid_string(pos.comment):
                comment = DealComment().set_from_string(pos.comment)
                if lieder_position.ticket == comment.lieder_ticket:
                    return True
    else:
        return False
    return False


def get_positions_profit():
    """Расчет прибыли текущих позиций"""
    active_positions = Mt.positions_get()

    # print('>>> ACTV: ')
    # for _ in active_positions:
    #     print(active_positions.index(_), datetime.fromtimestamp(_.time), _.profit)

    result = 0
    own_positions = []
    try:
        if len(active_positions) > 0:
            for pos in active_positions:
                if pos.magic == MAGIC:
                    own_positions.append(pos)
        if len(own_positions) > 0:
            for pos in own_positions:
                if pos.type < 2:
                    result += pos.profit  # + pos.commission
    except AttributeError:
        print('ERROR in get_positions_profit() : wrong positions list')
        result = None
    return result


def get_history_profit():
    """Расчет прибыли по истории"""
    date_from = start_date
    date_to = datetime.now().replace(microsecond=0) + UTC_OFFSET_TIMEDELTA

    history_deals = Mt.history_deals_get(date_from, date_to)

    # print('>>> HIST: ', date_from, ' - ', date_to)
    # for _ in history_deals:
    #     print(history_deals.index(_), datetime.fromtimestamp(_.time), _.profit)

    result = 0
    own_positions = []
    try:
        if len(history_deals) > 0:
            for pos in history_deals:
                if pos.magic == MAGIC and DealComment.is_valid_string(pos.comment):
                    linked_pos = Mt.history_deals_get(position=pos.position_id)
                    for lp in linked_pos:
                        own_positions.append(lp)
        if len(own_positions) > 0:
            for pos in own_positions:
                if pos.type < 2:
                    result += pos.profit  # + pos.commission
    except Exception as ex:
        print('ERROR get_history_profit():', ex)
        result = None
    return result


def check_stop_limits(investor):
    """Проверка стоп-лимита по проценту либо абсолютному показателю"""
    start_balance = investor['investment_size']
    if start_balance <= 0:
        start_balance = 1
    limit_size = investor['stop_value']
    calc_limit_in_percent = True if investor['stop_loss'] == 'Процент' else False
    history_profit = get_history_profit()
    current_profit = get_positions_profit()
    # SUMM TOTAL PROFIT
    if history_profit is None or current_profit is None:
        return
    close_positions = False
    total_profit = history_profit + current_profit

    # print(f'total_profit = history_profit + current_profit  ->  {total_profit} = {history_profit} + {current_profit}')

    print('\t', 'Прибыль' if total_profit >= 0 else 'Убыток', 'торговли c', start_date - UTC_OFFSET_TIMEDELTA,
          ':', round(total_profit, 2), 'USD')
    # CHECK LOST SIZE FOR CLOSE ALL
    if total_profit < 0:
        if calc_limit_in_percent:
            current_percent = fabs(total_profit / start_balance) * 100
            if current_percent >= limit_size:
                close_positions = True
        elif fabs(total_profit) >= limit_size:
            close_positions = True
        # CLOSE ALL POSITIONS
        if close_positions:
            print('     Закрытие всех позиций по условию стоп-лосс')
            set_comment('Закрытие всех позиций по условию стоп-лосс. Убыток торговли c' + str(start_date) + ':' +
                        str(round(total_profit, 2)) + 'USD')
            active_positions = Mt.positions_get()
            for act_pos in active_positions:
                if act_pos.magic == MAGIC:
                    close_position(act_pos, 'Закрытие позиции по условию стоп-лосс')
            if investor['open_trades'] == 'Закрыть и отключить':
                disable_dcs(source['investors'], investor)


def check_transaction(investor, lieder_position):
    """Проверка открытия позиции"""
    price_refund = True if investor['price_refund'] == 'Да' else False
    if not price_refund:  # если не возврат цены
        timeout = investor['waiting_time'] * 60
        deal_time = int(lieder_position.time_update - UTC_OFFSET_TIMEDELTA.seconds)
        curr_time = int(datetime.timestamp(datetime.now().replace(microsecond=0)))
        delta_time = curr_time - deal_time
        # print('=========', datetime.fromtimestamp(deal_time), datetime.fromtimestamp(curr_time), delta_time)
        if delta_time > timeout:  # если время больше заданного
            return False

    transaction_type = 0
    if investor['ask_an_investor'] == 'Плюс':
        transaction_type = 1
    elif investor['ask_an_investor'] == 'Минус':
        transaction_type = -1
    deal_profit = lieder_position.profit
    if transaction_type > 0 > deal_profit:  # если открывать только + и профит < 0
        return False
    if deal_profit > 0 > transaction_type:  # если открывать только - и профит > 0
        return False

    transaction_plus = investor['deal_in_plus']
    transaction_minus = investor['deal_in_minus']
    price_open = lieder_position.price_open
    price_current = lieder_position.price_current

    res = None
    if lieder_position.type == 0:  # Buy
        res = (price_current - price_open) / price_open * 100  # Расчет сделки покупки по формуле
    elif lieder_position.type == 1:  # Sell
        res = (price_open - price_current) / price_open * 100  # Расчет сделки продажи по формуле
    return True if res is not None and transaction_plus >= res >= transaction_minus else False  # Проверка на заданные отклонения


def get_deal_volume(investor, symbol, lieder_volume, lieder_balance_value):
    """Расчет множителя"""
    multiplier = investor['multiplier_value']
    investment_size = investor['investment_size']
    get_for_balance = True if investor['multiplier'] == 'Баланс' else False
    if get_for_balance:
        ext_k = (investment_size + get_history_profit()) / lieder_balance_value
    else:
        ext_k = (investment_size + get_history_profit() + get_positions_profit()) / lieder_balance_value
    try:
        min_lot = Mt.symbol_info(symbol).volume_min
        decimals = str(min_lot)[::-1].find('.')
    except AttributeError:
        decimals = 2
    result = round(lieder_volume * multiplier * ext_k, decimals)
    return result


def open_position(investor, symbol, deal_type, lot, sender_ticket: int, tp=0, sl=0):
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
    comment.reason = 'Открыто_СКС'
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
        "type_filling": Mt.ORDER_FILLING_RETURN,
    }
    checked_request = edit_volume(investor, request)  # Проверка и расчет объема при недостатке маржи
    if checked_request:
        result = Mt.order_send(checked_request)
        return result
    else:
        return {'retcode': -100}


def edit_volume(investor, request):
    """Расчет объема при недостатке маржи"""
    response = Mt.order_check(request)
    # print(response)
    if response.retcode == 10014:  # Неправильный объем
        max_vol = Mt.symbol_info(request['symbol']).volume_max
        if request['volume'] > max_vol:
            set_comment('Объем сделки больше максимального')
            request = None
    elif response.retcode == 10019:  # Нет достаточных денежных средств для выполнения запроса
        if source['investors']['not_enough_margin'] == 'Минимальный объем':
            request['volume'] = Mt.symbol_info(request['symbol']).volume_min
        elif source['investors']['not_enough_margin'] == 'Достаточный объем':
            symbol = request['symbol']
            contract_specification = Mt.symbol_info(symbol).contract_size
            price = Mt.symbol_info_tick(symbol).bid
            lot_price = contract_specification * price
            balance = investor['investment_size'] + get_history_profit() + get_positions_profit()
            min_lot = Mt.symbol_info(request.symbol).volume_min
            decimals = str(min_lot)[::-1].find('.')
            request['volume'] = round(balance / lot_price, decimals)
        elif source['investors']['not_enough_margin'] == 'Не открывать':
            request = None
    return request


def close_position(position, reason):
    """Закрытие указанной позиции"""
    tick = Mt.symbol_info_tick(position.symbol)
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
        'comment': new_comment_str,  # 'CLOSED_BY_EXPERT',
        'type_tim': Mt.ORDER_TIME_GTC,
        'type_filing': Mt.ORDER_FILLING_IOC
    }
    result = Mt.order_send(request)
    return result


def force_close_all_positions(investor, reason):
    """Принудительное закрытие всех позиций аккаунта"""
    init_res = init_mt(init_data=investor)
    if init_res:
        positions = Mt.positions_get()
        if len(positions) > 0:
            for position in positions:
                if position.magic == MAGIC and DealComment.is_valid_string(position.comment):
                    close_position(position, reason=reason)
        Mt.shutdown()


def close_positions_by_lieder(positions_lieder, positions_investor):
    """Закрытие позиций инвестора, которые закрылись у лидера"""
    non_existed_positions = []
    for ip in positions_investor:
        position_exist = False
        for lp in positions_lieder:
            if DealComment.is_valid_string(ip.comment):
                comment = DealComment().set_from_string(ip.comment)
                if comment.lieder_ticket == lp.ticket:
                    position_exist = True
                    break
        if not position_exist:
            non_existed_positions.append(ip)
    for pos in non_existed_positions:
        print('     close position:', pos.comment)
        close_position(pos, reason='Закрыто инвестором')


def check_notification():
    if source['notification'] == 'Да':
        set_comment('Вы должны оплатить вознаграждение')


async def source_setup():
    global start_date, source
    main_source = {}
    url = host + 'last'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as get_response:
                response = await get_response.json()  # .text()
    except Exception as e:
        print(e)
        response = []
    if len(response) > 0:
        response = response[0]
        main_source['lieder'] = {
            'terminal_path': r'C:\Program Files\MetaTrader 5\terminal64.exe',
            'login': int(response['leader_login']),
            'password': response['leader_password'],
            'server': response['leader_server']
        }
        main_source['investors'] = [
            {
                'terminal_path': r'C:\Program Files\MetaTrader 5_2\terminal64.exe',
                'login': int(response['investor_one_login']),
                'password': response['investor_one_password'],
                'server': response['investor_one_server'],
                'investment_size': float(response['investment_one_size']),
                'dcs_access': response['access_1'],

                "deal_in_plus": float(response['deal_in_plus']),
                "deal_in_minus": float(response['deal_in_minus']),
                "waiting_time": int(response['waiting_time']),
                "ask_an_investor": response['ask_an_investor'],
                "price_refund": response['price_refund'],
                "multiplier": response['multiplier'],
                "multiplier_value": float(response['multiplier_value']),
                "changing_multiplier": response['changing_multiplier'],
                "stop_loss": response['stop_loss'],
                "stop_value": float(response['stop_value']),
                "open_trades": response['open_trades'],
                "shutdown_initiator": response['shutdown_initiator'],
                "disconnect": response['disconnect'],
                'disconnect_previous': response['disconnect'],

                "open_trades_disconnect": response['open_trades_disconnect'],
                "notification": response['notification'],
                "blacklist": response['blacklist'],
                "accompany_transactions": response['accompany_transactions'],
                "no_exchange_connection": response['no_exchange_connection'],
                "api_key_expired": response['api_key_expired'],
                "closed_deals_myself": response['closed_deals_myself'],
                "reconnected": response['reconnected'],
                "recovery_model": response['recovery_model'],
                "buy_hold_model": response['buy_hold_model'],
                "not_enough_margin": response['not_enough_margin'],
                "accounts_in_diff_curr": response['accounts_in_diff_curr'],
                "synchronize_deals": response['synchronize_deals'],
                "deals_not_opened": response['deals_not_opened'],
                "closed_deal_investor": response['closed_deal_investor'],
                "opening_deal": response['opening_deal'],
                "closing_deal": response['closing_deal'],
                "target_and_stop": response['target_and_stop'],
                "signal_relevance": response['signal_relevance'],
                "profitability": response['profitability'],
                "risk": response['risk'],
                "profit": response['profit'],
                "comment": response['comment'],
            },
            {
                'terminal_path': r'C:\Program Files\MetaTrader 5_3\terminal64.exe',
                'login': int(response['investor_two_login']),
                'password': response['investor_two_password'],
                'server': response['investor_two_server'],
                'investment_size': float(response['investment_two_size']),
                'dcs_access': response['access_2'],
                'dcs_access_previous': response['access_2'],

                "deal_in_plus": float(response['deal_in_plus']),
                "deal_in_minus": float(response['deal_in_minus']),
                "waiting_time": int(response['waiting_time']),
                "ask_an_investor": response['ask_an_investor'],
                "price_refund": response['price_refund'],
                "multiplier": response['multiplier'],
                "multiplier_value": float(response['multiplier_value']),
                "changing_multiplier": response['changing_multiplier'],
                "stop_loss": response['stop_loss'],
                "stop_value": float(response['stop_value']),
                "open_trades": response['open_trades'],
                "shutdown_initiator": response['shutdown_initiator'],
                "disconnect": response['disconnect'],
                'disconnect_previous': response['disconnect'],

                "open_trades_disconnect": response['open_trades_disconnect'],
                "notification": response['notification'],
                "blacklist": response['blacklist'],
                "accompany_transactions": response['accompany_transactions'],
                "no_exchange_connection": response['no_exchange_connection'],
                "api_key_expired": response['api_key_expired'],
                "closed_deals_myself": response['closed_deals_myself'],
                "reconnected": response['reconnected'],
                "recovery_model": response['recovery_model'],
                "buy_hold_model": response['buy_hold_model'],
                "not_enough_margin": response['not_enough_margin'],
                "accounts_in_diff_curr": response['accounts_in_diff_curr'],
                "synchronize_deals": response['synchronize_deals'],
                "deals_not_opened": response['deals_not_opened'],
                "closed_deal_investor": response['closed_deal_investor'],
                "opening_deal": response['opening_deal'],
                "closing_deal": response['closing_deal'],
                "target_and_stop": response['target_and_stop'],
                "signal_relevance": response['signal_relevance'],
                "profitability": response['profitability'],
                "risk": response['risk'],
                "profit": response['profit'],
                "comment": response['comment'],
            }
        ]
        main_source['settings'] = {
            "relevance": response['relevance'],
            "update_at": response['update_at'],
            "created_at": response['created_at']
            # "access": response['access'],
        }
        prev_date = main_source['settings']['created_at'].split('.')
        start_date = datetime.strptime(prev_date[0], "%Y-%m-%dT%H:%M:%S")
    source = main_source.copy()


async def patching_quotes():
    utc_to = datetime.combine(datetime.today(), datetime.min.time())
    utc_from = utc_to - timedelta(days=1)
    quotes = ['EURUSD', 'USDRUB', 'EURRUB']
    for i, quote in enumerate(quotes):
        i = i + 1
        try:
            if quote == 'EURRUB':
                eurusd = Mt.copy_rates_range("EURUSD", Mt.TIMEFRAME_H4, utc_from, utc_to)[-1][4]
                usdrub = Mt.copy_rates_range("USDRUB", Mt.TIMEFRAME_H4, utc_from, utc_to)[-1][4]
                data = {"currencies": quote,
                        "close": eurusd * usdrub}
            else:
                data = {"currencies": quote,
                        "close": Mt.copy_rates_range(quote, Mt.TIMEFRAME_H4, utc_from, utc_to)[-1][4]}
            payload = json.dumps(data,
                                 sort_keys=True,
                                 indent=1,
                                 cls=DjangoJSONEncoder)
            headers = {'Content-Type': 'application/json'}
            patch_url = f'http://127.0.0.1:8000/exchange/update/{i}/'
            requests.request("PATCH", patch_url, headers=headers, data=payload)
        except Exception as e:
            print("Exception in patching_quotes:", e)


async def patching_connection_exchange():
    try:
        api_key_expired = source['investors'][0]['api_key_expired']
        no_exchange_connection = source['investors'][0]['no_exchange_connection']
        comment_json = source['investors'][0]['comment']
        if api_key_expired == "Да":
            comment = 'Ключ APi истек'
            for investor in source['investors']:
                force_close_all_positions(investor=investor, reason=comment)
        elif no_exchange_connection == 'Да':
            comment = 'Нет связи с биржей'
            for investor in source['investors']:
                force_close_all_positions(investor=investor, reason=comment)
        else:
            comment = comment_json
        set_comment(comment=comment)
    except Exception as e:
        print("Exception in patching_connection_exchange:", e)


async def update_setup():
    while True:
        await source_setup()
        await asyncio.sleep(.1)


async def update_lieder_info(sleep=sleep_lieder_update):
    global lieder_balance, lieder_equity, lieder_positions, source
    while True:
        if len(source) > 0:
            init_res = init_mt(init_data=source['lieder'])
            if not init_res:
                set_comment('Ошибка инициализации лидера')
                await asyncio.sleep(sleep)
                continue
            lieder_balance = Mt.account_info().balance
            lieder_equity = Mt.account_info().equity
            lieder_positions = Mt.positions_get()
            Mt.shutdown()
            # print(lieder_positions)
            # print(f'\nLIEDER {source["lieder"]["login"]} - {len(lieder_positions)} positions :',
            #      datetime.utcnow().replace(microsecond=0), ' dUTC:', UTC_OFFSET_TIMEDELTA,
            #      ' Comments:', send_messages)
            trading_event.set()
            send_signals()
        await asyncio.sleep(sleep)


def is_position_opened(lieder_position, investor):
    """Проверка позиции лидера на наличие в списке позиций инвестора"""
    if is_position_exist_in_list(lieder_position=lieder_position, investor_positions=Mt.positions_get()):
        return True
    if is_position_exist_in_history(lieder_position=lieder_position):
        if investor['closed_deals_myself'] == 'Переоткрывать':
            return False
        return True
    return False


async def execute_investor(investor):
    init_res = init_mt(init_data=investor)
    if not init_res:
        set_comment('Ошибка инициализации инвестора ' + str(investor['login']))
        return
    # enable_algotrading()
    global output_report
    output_report = []
    print(f' - {investor["login"]} - {len(Mt.positions_get())} positions. Access:', investor['dcs_access'])
    if investor['dcs_access']:
        execute_conditions(investor=investor)  # проверка условий кейса закрытия
        for pos_lid in lieder_positions:
            inv_tp = get_pips_tp(pos_lid)
            inv_sl = get_pips_sl(pos_lid)
            if not is_position_opened(pos_lid, investor):
                if check_transaction(investor=investor, lieder_position=pos_lid):
                    volume = 1.0 \
                        if investor['changing_multiplier'] == 'Нет' \
                        else get_deal_volume(investor, symbol=pos_lid.symbol, lieder_volume=pos_lid.volume,
                                             lieder_balance_value=lieder_balance
                                             if investor['multiplier'] == 'Баланс' else lieder_equity)
                    response = open_position(investor=investor, symbol=pos_lid.symbol, deal_type=pos_lid.type,
                                             lot=volume, sender_ticket=pos_lid.ticket, tp=inv_tp, sl=inv_sl)
                    try:
                        msg = str(investor['login']) + ' ' + send_retcodes[response.retcode][1] + ' : ' + str(
                            response.retcode)
                    except AttributeError:
                        msg = str(investor['login']) + ' ' + send_retcodes[response['retcode']][1] + ' : ' + str(
                            response['retcode'])
                    try:
                        ret_code = response.retcode
                    except AttributeError:
                        ret_code = response['retcode']

                    if ret_code != 10009:  # Заявка выполнена
                        set_comment(msg)
                    print(msg)
                else:
                    set_comment('Не выполнено условие +/-')
        check_stop_limits(investor=investor)  # проверка условий стоп-лосс
    else:
        print('ACCESS DISABLED')

    # закрытие позиций от лидера
    if investor['dcs_access'] or \
            (not investor['dcs_access']
             and investor['accompany_transactions'] == 'Да'):  # если сопровождать сделки или доступ есть
        close_positions_by_lieder(positions_lieder=lieder_positions,
                                  positions_investor=Mt.positions_get())

    Mt.shutdown()


async def correcting_lots():
    try:
        response_source = dict(requests.get(host + 'last').json()[0])
        if "Корректировать объем" in (response_source.get("recovery_model"), response_source.get("buy_hold_model")):
            # investors_balance = [x.get("investment_size") for x in investors_list]
            investors_balance = [source['investors'][0].get("investment_size"),
                                 source['investors'][1].get("investment_size")]
            global old_investors_balance
            if not old_investors_balance:
                old_investors_balance = investors_balance
            if investors_balance != old_investors_balance:
                lots_qoef = [x / y for x, y in zip(investors_balance, old_investors_balance)]
                for i, qoef in enumerate(lots_qoef):
                    if qoef != 1.0:
                        for pos in investor_positions:
                            print(pos)
                            # inv_tp = get_pips_tp(pos_lid)
                            # inv_sl = get_pips_sl(pos_lid)
                            # for investor in source['investors']:
                            #     volume = get_deals_volume(investor, lieder_volume=pos_lid.volume,
                            #                               lieder_balance_value=lieder_balance
                            #                               if settings['multiplier'] == 'Баланс' else lieder_equity)
                old_investors_balance = investors_balance

    except Exception as e:
        print("Exception in correcting_lots:", e)


async def task_manager():
    global investor_positions
    while True:
        await trading_event.wait()
        if len(source) > 0:
            for i, _ in enumerate(source['investors']):
                event_loop.create_task(execute_investor(_))
                investor_positions[f"investor{i + 1}"] = Mt.positions_get()
        time_now = datetime.now()
        current_time = time_now.strftime("%H:%M:%S")
        # await correcting_lots()
        await patching_connection_exchange()
        if current_time == "10:00:00":
            await patching_quotes()
        trading_event.clear()


def create_signal_json(lieder_position, status):
    return {'ticket': lieder_position[0],
            'type_ticket': '???',
            'status': status,
            'pattern': 'Из стратегии',
            'signal_class': 'Из стратегии',
            'signal_symbol': lieder_position[16],  # symbol
            'leverage': None,
            'open_price': lieder_position[10],  # price_open
            'goal': lieder_position[11],  # sl
            'goal_value': None,
            'stop_value': lieder_position[12],  # tp
            'stop': None,
            'profitability': lieder_position[15],  # profit
            'close_date': None,
            'fin_res': None,
            'draw_down': None}


def send_signals():
    global lieder_positions, listed_signals
    positions = lieder_positions
    listed = listed_signals

    new_positions = []
    for position in positions:
        new_positions.append(position)
        for signal in listed_signals:
            if position[0] == signal[0]:
                new_positions.remove(position)

    if new_positions:
        for new_position in new_positions:
            data = create_signal_json(new_position, True)
            # TODO: Вынести в общий параметр
            url = f'http://127.0.0.1:8000/api/create_signal'
            response = requests.post(url, data=data)
            if response.status_code == 201 or response.status_code == 400:
                listed_signals.append(new_position)

    old_positions = []
    for signal in listed_signals:
        old_positions.append(signal)
        for position in positions:
            if position[0] == signal[0]:
                old_positions.remove(signal)

    if old_positions:
        for old_position in old_positions:
            data = create_signal_json(old_position, False)
            # TODO: Вынести в общий параметр
            url = f'http://127.0.0.1:8000/api/update_signal/{old_position[0]}'
            response = requests.put(url, data=data)
            print(response.status_code)
            if response.status_code == 200:
                listed_signals.remove(old_position)

    # print(listed_signals)


if __name__ == '__main__':
    print(f'\nСКС запущена [{start_date}]. Обновление Лидера {sleep_lieder_update} с.')
    set_dummy_data()  # для теста без сервера раскомментировать
    event_loop = asyncio.new_event_loop()
    # event_loop.create_task(update_setup())  # для теста без сервера закомментировать
    event_loop.create_task(update_lieder_info())
    # event_loop.create_task(task_manager())
    # event_loop.create_task(send_signals())
    event_loop.run_forever()
    Mt.shutdown()
