import asyncio
from datetime import datetime, timedelta
import aiohttp
from terminal import init_mt, get_lieder_positions, close_positions_by_lieder, open_position, send_retcodes, \
    is_position_opened, close_position, get_investor_position_for_signal, start_date, \
    is_lieder_position_in_investor_history, get_investor_positions

trading_event = asyncio.Event()  # init async event
lieder_signals = []  # default var
signals_settings = {}  # default var
source = {}

sleep_update = 3  # пауза для обновления лидера

host = 'http://127.0.0.1:8000/api/'


def reset_source(only_investors=False):
    global source
    if only_investors:
        source['investors'] = []
    else:
        source = {
            # 'lieder': {}
            # 'investors': [{}, {}],
            # 'signals': [[{}, {}], [{}, {}]],
            # 'terminals_path': [str, str]
            'lieder': {'login': 66587203,
                       'password': '3hksvtko',
                       'server': 'MetaQuotes-Demo',
                       'terminal_path': r'C:\Program Files\MetaTrader 5\terminal64.exe'},
            'investors': [],
            'signals': [],
            'terminals_path': [r'C:\Program Files\MetaTrader 5_2\terminal64.exe',
                               r'C:\Program Files\MetaTrader 5_3\terminal64.exe']}


def get_investor_id(investor):
    for _ in source['investors']:
        if _['login'] == investor['login']:
            return source['investors'].index(_)
    return -1


def get_investor_data(investor):
    idx = get_investor_id(investor)
    if idx < 0:
        return {}, {}
    else:
        init_data = {'login': source['investors'][idx]['login'],
                     'server': source['investors'][idx]['server'],
                     'password': source['investors'][idx]['password'],
                     'terminal_path': source['terminals_path'][idx]}
        settings = {'multiplier': source['investors'][idx]['multiplier'],
                    'state': source['investors'][idx]['state'],
                    'target_value': source['investors'][idx]['target_value'],
                    'stop_value': source['investors'][idx]['stop_value'],
                    'opening_deal': source['investors'][idx]['opening_deal'],
                    'closing_deal': source['investors'][idx]['closing_deal'],
                    'target_and_stop': source['investors'][idx]['target_and_stop'],
                    'risk': source['investors'][idx]['risk'],
                    'signal_relevance': source['investors'][idx]['signal_relevance'],
                    'profit': source['investors'][idx]['profit']}
        return init_data, settings, idx


def create_signal_json(lieder_position, status):
    return {'ticket': lieder_position.ticket,
            'deal_type': lieder_position.type,
            'current_price': lieder_position.price_current,
            'signal_symbol': lieder_position.symbol,
            'open_price': lieder_position.price_open,
            'goal': lieder_position.tp,
            'stop_value': lieder_position.sl,
            'profitability': lieder_position.profit,
            'status': status, }
    # 'type_ticket': '???',
    # 'pattern': 'Из стратегии',
    # 'signal_class': 'Из стратегии',
    # 'leverage': -1,
    # 'goal_value': -1,
    # 'stop': -1,
    # 'close_date': -1,
    # 'fin_res': -1,
    # 'draw_down': -1}


def is_signal_actual(signal_item):
    price_open = signal_item['open_price']
    price_current = signal_item['current_price']
    deviation = signal_item['signal_relevance']
    deal_type = signal_item['deal_type']
    percent = price_open / 100
    if deal_type == 0:  # BUY
        actual_level = (price_open - price_current) / percent
    else:  # SELL
        actual_level = (price_current - price_open) / percent
    # print(signal_item['signal_symbol'], deal_type, price_open, price_current, actual_level)
    return actual_level < deviation


async def get_settings(sleep=sleep_update):
    global signals_settings, source
    url = host + 'signals_settings'
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as get_response:
                    response = await get_response.json()
        except Exception as e:
            print(e)
            response = {}
        if len(response):
            reset_source(only_investors=True)
            signals_settings = response[0]
            investor_data_first = {'login': signals_settings['investor_login_1'],
                                   'password': signals_settings['investor_password_1'],
                                   'server': signals_settings['investor_server_1'],
                                   'investment': signals_settings['investment_1'],
                                   'multiplier': signals_settings['multiplier'],
                                   'state': signals_settings['state'],
                                   'target_value': signals_settings['target_value'],
                                   'stop_value': signals_settings['stop_value'],
                                   'opening_deal': signals_settings['opening_deal'],
                                   'closing_deal': signals_settings['closing_deal'],
                                   'target_and_stop': signals_settings['target_and_stop'],
                                   'profitability': signals_settings['profitability'],
                                   'risk': signals_settings['risk'],
                                   'profit': signals_settings['profit'],
                                   'signal_relevance': signals_settings['signal_relevance']}
            source['investors'].append(investor_data_first)
            investor_data_second = investor_data_first.copy()
            investor_data_second['login'] = signals_settings['investor_login_2']
            investor_data_second['password'] = signals_settings['investor_password_2']
            investor_data_second['server'] = signals_settings['investor_server_2']
            investor_data_second['investment'] = signals_settings['investment_2']
            source['investors'].append(investor_data_second)
        else:
            reset_source()
        await asyncio.sleep(sleep)


def synchronize_signal_list(investor, settings):
    investor_id = get_investor_id(investor)
    for signal in lieder_signals:
        signal.update(settings)  # сложить данные о сигнале лидера и настроек инвестора

        if len(source['signals']) - 1 < investor_id:
            source['signals'].append([])  # увеличить длину списка сигналов если он меньше текущего сигнала лидера

        exist_signal_id = -1  # Поиск сигнала лидера в имеющемся списке сигналов
        investor_signals = source['signals'][investor_id]
        for _ in investor_signals:
            signal_id = investor_signals.index(_)
            if investor_signals[signal_id]['ticket'] == signal['ticket']:
                exist_signal_id = signal_id
                break

        if exist_signal_id < 0:  # Если сигнал не найден, добавить в список
            source['signals'][investor_id].append(signal)
        else:  # Иначе обновить цену и профит сигнала
            source['signals'][investor_id][exist_signal_id]['current_price'] = signal['current_price']
            source['signals'][investor_id][exist_signal_id]['profitability'] = signal['profitability']

    investor_signals = source['signals'][investor_id]  # удалить отсутствующие сигналы лидера
    for inv_signal in investor_signals:
        exist_signal_id = -1
        for lid_signal in lieder_signals:
            if inv_signal['ticket'] == lid_signal['ticket']:
                exist_signal_id = lieder_signals.index(lid_signal)
                break
        if exist_signal_id < 0:
            investor_signals.remove(investor_signals[investor_signals.index(inv_signal)])
    return source['signals'][investor_id]


async def send_lieder_signals(sleep=sleep_update):
    global lieder_signals
    url_post = host + 'create_signal'
    while True:
        lieder_positions = get_lieder_positions(lieder_init_data=source['lieder'])
        lieder_signals = []
        if lieder_positions:
            try:
                for position in lieder_positions:
                    data_json = create_signal_json(position, True)
                    lieder_signals.append(data_json)
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url=url_post, data=data_json) as resp_post:
                            await resp_post.json()
                            if resp_post.status == 400:
                                url = host + f'update_signal/{data_json["ticket"]}'
                                data = {'current_price': data_json['current_price'],
                                        'profitability': data_json['profitability']}
                                async with session.patch(url=url, data=data) as resp_patch:
                                    await resp_patch.json()
                            # if resp_post.status == 200 or resp_patch.status == 200:
                            #     lid_positions.remove(position)
                trading_event.set()
            except Exception as e:
                print('send_lieder_signals()', e)
        print(
            f'\n\tЛидер [{source["lieder"]["login"]}] {datetime.now().time()} - {len(lieder_signals)} активных сигнала')
        await asyncio.sleep(sleep)


async def execute_investor(investor):
    investor_init_data, investor_settings, investor_id = get_investor_data(investor)
    if not init_mt(init_data=investor_init_data):
        return
    signal_list = synchronize_signal_list(investor, investor_settings)
    # ---------------------------------------------------------------------------   Открытие
    for signal in signal_list:

        if signal['opening_deal'] in ['Пропуск', 'Не выбрано']:  # Пропустить по настройкам
            continue
        if is_position_opened(signal):  # Пропустить если уже открыта
            continue
        if is_lieder_position_in_investor_history(signal):  # Пропустить если уже была открыта (в истории)
            print(f'\t\tПозиция по сигналу {signal["ticket"]} закрыта ранее инвестором [{investor["login"]}]')
            continue
        if not is_signal_actual(signal):  # Пропустить если сигнал неактуален
            print(f'\t\tСигнал {signal["ticket"]} неактуален')
            continue

        response = open_position(symbol=signal['signal_symbol'], deal_type=signal['deal_type'],
                                 lot=.01, sender_ticket=signal['ticket'])
        if response:
            try:
                ret_code = response.retcode
            except AttributeError:
                ret_code = response['retcode']
            if ret_code:
                deal_type = 'BUY' if signal['deal_type'] == 0 else 'SELL'
                msg = f'\t --- [{investor["login"]}] {deal_type} {send_retcodes[ret_code][1]}:{ret_code} : сигнал {signal["ticket"]}'
                print(msg)
        else:
            print('EMPTY_RESPONSE_FOR_DEAL_OPEN')
    # ---------------------------------------------------------------------------  Закрытие
    for signal in signal_list:

        if signal['closing_deal'] in ['Пропуск', 'Не выбрано']:  # Пропустить по настройкам
            continue

        if signal['closing_deal'] == 'Закрыть':  # Ручное закрытие через инвест платформу
            position = get_investor_position_for_signal(signal)
            if position:
                close_position(position=position, reason='10')

        # if signal['closing_deal'] == 'Закрыть':  # Ручное закрытие через инвест платформу

    print(signal_list)
    print(f'\tИнвестор [{investor["login"]}] {datetime.now().time()} - {len(get_investor_positions())} позиций')


async def task_manager():
    while True:
        await trading_event.wait()

        if len(source['investors']) > 0:
            for _ in source['investors']:
                event_loop.create_task(execute_investor(_))

        trading_event.clear()


if __name__ == '__main__':
    reset_source()
    print(f'\nСистема сигналов [{start_date}]. Обновление Лидера [{source["lieder"]["login"]}] {sleep_update} с.')
    event_loop = asyncio.new_event_loop()
    event_loop.create_task(get_settings())
    event_loop.create_task(send_lieder_signals())
    event_loop.create_task(task_manager())
    event_loop.run_forever()
