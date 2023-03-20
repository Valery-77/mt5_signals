from datetime import datetime, timedelta
import MetaTrader5 as Mt
from math import fabs, floor

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
    '001': 'Открыто Системой сигналов',
    '002': 'Ручное закрытие через инвест платформу',
    '003': 'Закрыто Лидером',
    '004': 'Лимиты изменены',
    # '03': 'Закрыто по команде пользователя',
    # '06': 'Закрыто инвестором',
    # '09': 'Лимиты изменены',
    # '10': 'Ручное закрытие через инвест платформу',
}

TIMEOUT_INIT = 60_000  # время ожидания при инициализации терминала (рекомендуемое 60_000 millisecond)
MAGIC = 9876543210  # идентификатор эксперта
DEVIATION = 20  # допустимое отклонение цены в пунктах при совершении сделки
start_date = datetime.now().replace(microsecond=0)
SERVER_DELTA_TIME = timedelta(hours=0)


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


def init_mt(init_data):
    """Инициализация терминала"""
    result = Mt.initialize(login=init_data['login'], server=init_data['server'], password=init_data['password'],
                           path=init_data['terminal_path'], timeout=TIMEOUT_INIT)
    if not result:
        print(f'\t !!! {init_data["login"]} - Ошибка инициализации - {init_data["terminal_path"]}')
    return result


def get_signal_pips_tp(signal):
    """Расчет Тейк-профит в пунктах"""
    symbol = signal['signal_symbol']
    level = signal['target_value']
    price = signal['open_price']
    result = 0.0
    if level > 0:
        result = round(fabs(price - level) / Mt.symbol_info(symbol).point)
    return result


def get_signal_pips_sl(signal):
    """Расчет Стоп-лосс в пунктах"""
    result = 0.0
    if signal['stop_value'] > 0:
        result = round(
            fabs(signal['open_price'] - signal['stop_value']) / Mt.symbol_info(signal['signal_symbol']).point)
    return result


def get_position_pips_tp(position, price=None):
    """Расчет Тейк-профит в пунктах"""
    if price is None:
        price = position.price_open
    result = 0.0
    if position.tp > 0:
        result = round(fabs(price - position.tp) / Mt.symbol_info(position.symbol).point)
    return result


def get_position_pips_sl(position, price=None):
    """Расчет Стоп-лосс в пунктах"""
    if price is None:
        price = position.price_open
    result = 0.0
    if position.sl > 0:
        result = round(fabs(price - position.sl) / Mt.symbol_info(position.symbol).point)
    return result


def get_lieder_positions(lieder_init_data):
    if init_mt(lieder_init_data):
        return Mt.positions_get()
    return None


def get_investor_positions(only_own=True):
    result = []
    positions = Mt.positions_get()
    if not positions:
        return []
    if only_own and len(positions) > 0:
        for _ in positions:
            if positions[positions.index(_)].magic == MAGIC and DealComment.is_valid_string(_.comment):
                result.append(_)
    else:
        result = positions
    return result


def is_position_opened(lieder_position):
    """Проверка позиции лидера на наличие в списке позиций и истории инвестора"""
    # init_mt(init_data=investor)
    invest_positions = get_investor_positions(only_own=False)
    if len(invest_positions) > 0:
        for pos in invest_positions:
            if DealComment.is_valid_string(pos.comment):
                comment = DealComment().set_from_string(pos.comment)
                if lieder_position['ticket'] == comment.lieder_ticket:
                    return True
    return False


def is_lieder_position_in_investor_history(signal):
    date_from = start_date + SERVER_DELTA_TIME
    date_to = datetime.today().replace(microsecond=0) + timedelta(days=1)
    # print(date_from, date_to)
    deals = Mt.history_deals_get(date_from, date_to)
    # print(deals)
    if not deals:
        deals = []
    result = None
    if len(deals) > 0:
        for pos in deals:
            if DealComment.is_valid_string(pos.comment):
                comment = DealComment().set_from_string(pos.comment)
                if signal['ticket'] == comment.lieder_ticket:
                    result = pos
                    break
    return result


def open_position(symbol, deal_type, lot, lieder_position_ticket: int, tp=0.0, sl=0.0):
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
    comment.lieder_ticket = lieder_position_ticket
    comment.reason = '001'
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
    print(request)
    result = Mt.order_send(request)
    return result


def close_position(investor, position, reason):
    """Закрытие указанной позиции"""
    # if investor:
    #     init_mt(init_data=investor)
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
    if comment:
        print(
            f'\t\t -- [{investor["login"]}] - {comment.lieder_ticket} {reasons_code[reason]} - {send_retcodes[result.retcode][1]}')
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


def close_positions_by_lieder(investor, lieder_positions):
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
        close_position(investor=investor, position=pos, reason='06')


def close_signal_position(signal, reason):
    """Закрытие позиции инвестора"""
    positions_investor = get_investor_positions()
    if positions_investor:
        for ip in positions_investor:
            comment = DealComment().set_from_string(ip.comment)
            if signal['ticket'] == comment.lieder_ticket:
                close_position(position=ip, reason=reason)


def close_investor_positions(signal_list):
    """Закрытие позиций инвесторов по сопровождению"""
    for signal in signal_list:
        if signal['opening_deal'] == 'Сопровождение' or signal['closing_deal'] == 'Сопровождение':
            close_signal_position(signal=signal, reason='06')


def get_investor_position_for_signal(signal):
    positions = get_investor_positions()
    for _ in positions:
        pos_comment = DealComment().set_from_string(_.comment)
        if pos_comment.lieder_ticket == signal['ticket']:
            return _
    return None


def get_lots_for_investment(symbol, investment):
    # investment = 1259
    # smb = 'GBPUSD'
    print(
        f'\nsymbol: {symbol}')  # currency_base: {Mt.symbol_info(smb).currency_base}  currency_profit: {Mt.symbol_info(smb).currency_profit}  currency_margin: {Mt.symbol_info(smb).currency_margin}')
    price = Mt.symbol_info_tick(symbol).bid
    leverage = Mt.account_info().leverage
    contract = Mt.symbol_info(symbol).trade_contract_size

    min_lot = Mt.symbol_info(symbol).volume_min
    lot_step = Mt.symbol_info(symbol).volume_step
    decimals = str(lot_step)[::-1].find('.')

    volume_none_round = (investment * leverage) / (contract * price)
    # volume = floor((investment * leverage) / (contract * price) / lot_step) * lot_step
    # print(floor((investment * leverage) / (contract * price) / lot_step), lot_step)
    # print(f'Неокругленный объем: {volume_none_round}  Округленный объем: {volume}')
    if volume_none_round < min_lot:
        volume = 0.0
    else:
        volume = round(floor(volume_none_round / lot_step) * lot_step, decimals)

    print(
        f'Размер инвестиции: {investment}  Курс: {price}  Контракт: {contract}  Плечо: {leverage}  >>  ОБЪЕМ: {volume}')

    # calc_margin = Mt.order_calc_margin(0, symbol, volume, price)
    # print('Стоимость сделки:', calc_margin,
    #       f' Остаток: {round(investment - calc_margin, 2)}' if calc_margin else 'Не хватает средств')
    return volume


def synchronize_position_limits(signal):
    """Изменение уровней ТП и СЛ указанной позиции"""
    i_pos = get_investor_position_for_signal(signal)
    if not i_pos:
        return
    l_tp = get_signal_pips_tp(signal)
    l_sl = get_signal_pips_sl(signal)
    if l_tp > 0 or l_sl > 0:
        request = []
        new_comment_str = comment = ''
        if DealComment.is_valid_string(i_pos.comment):
            comment = DealComment().set_from_string(i_pos.comment)
            comment.reason = '004'
            new_comment_str = comment.string()
        if comment.lieder_ticket == signal['ticket']:
            i_tp = get_position_pips_tp(i_pos)
            i_sl = get_position_pips_sl(i_pos)
            sl_lvl = tp_lvl = 0.0
            point = Mt.symbol_info(i_pos.symbol).point
            if i_pos.type == Mt.POSITION_TYPE_BUY:
                sl_lvl = i_pos.price_open - l_sl * point if l_sl > 0 else 0.0
                tp_lvl = i_pos.price_open + l_tp * point if l_tp > 0 else 0.0
            elif i_pos.type == Mt.POSITION_TYPE_SELL:
                sl_lvl = i_pos.price_open + l_sl * point if l_sl > 0 else 0.0
                tp_lvl = i_pos.price_open - l_tp * point if l_tp > 0 else 0.0
            if i_tp != l_tp or i_sl != l_sl:
                request = {
                    "action": Mt.TRADE_ACTION_SLTP,
                    "position": i_pos.ticket,
                    "symbol": i_pos.symbol,
                    "sl": sl_lvl,
                    "tp": tp_lvl,
                    "magic": MAGIC,
                    "comment": new_comment_str
                }
        if request:
            result = Mt.order_send(request)
            print('Изменение лимитов::', result)


def is_symbol_allow(symbol):
    all_symbols = Mt.symbols_get()
    symbol_names = []
    for symbol_ in all_symbols:
        symbol_names.append(symbol_.name)

    if symbol in symbol_names:
        if Mt.symbol_select(symbol, True):
            return True
        else:
            return False
    else:
        return False
