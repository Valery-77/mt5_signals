import asyncio

import aiohttp
from terminal import *

signals_exist_event = asyncio.Event()  # init async event
exist_lieder_signals = new_lieder_signals = []  # default var
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
        return {}, {}, idx
    else:
        init_data = {'login': source['investors'][idx]['login'],
                     'server': source['investors'][idx]['server'],
                     'password': source['investors'][idx]['password'],
                     'terminal_path': source['terminals_path'][idx]}
        settings = {'multiplier': source['investors'][idx]['multiplier'],
                    'investment': source['investors'][idx]['investment'],
                    'state': source['investors'][idx]['state'],
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
            'target_value': lieder_position.tp,
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


def is_signal_relevance(signal_item):
    price_open = signal_item['open_price']
    price_current = signal_item['current_price']
    deviation = signal_item['signal_relevance']
    deal_type = signal_item['deal_type']
    percent = price_open / 100
    if deal_type == 0:  # BUY
        actual_level = (price_open - price_current) / percent
    else:  # SELL
        actual_level = (price_current - price_open) / percent
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
                                   # 'target_value': signals_settings['target_value'],
                                   # 'stop_value': signals_settings['stop_value'],
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


def synchronize_signal_list(investor, signal_settings):
    investor_id = get_investor_id(investor)
    #   ------------------------------------------------    Добавление и обновление сигналов инвестора
    for signal_ in new_lieder_signals:
        signal = signal_.copy()
        signal.update(signal_settings)  # сложить данные о сигнале лидера и настроек сигнала инвестора

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
        else:  # Иначе обновить цену, лимиты и профит сигнала
            source['signals'][investor_id][exist_signal_id]['current_price'] = signal['current_price']
            source['signals'][investor_id][exist_signal_id]['profitability'] = signal['profitability']
            source['signals'][investor_id][exist_signal_id]['target_value'] = signal['target_value']
            source['signals'][investor_id][exist_signal_id]['stop_value'] = signal['stop_value']
    investor_signals = source['signals'][investor_id]
    #   ------------------------------------------------    Удаление отсутствующих сигналов лидера
    for inv_signal in investor_signals:
        exist_signal_id = -1
        for lid_signal in new_lieder_signals:
            if inv_signal['ticket'] == lid_signal['ticket']:
                exist_signal_id = new_lieder_signals.index(lid_signal)
                break
        if exist_signal_id < 0:
            investor_signals.remove(investor_signals[investor_signals.index(inv_signal)])

    return source['signals'][investor_id]


def disable_closed_positions_signals():
    """Отправка статуса"""
    global exist_lieder_signals, new_lieder_signals
    close_position_signal_list = []

    for old_signal in exist_lieder_signals:  # Отправка статуса и даты закрытия
        signal_exist = False
        for new_signal in new_lieder_signals:
            if old_signal['ticket'] == new_signal['ticket']:
                signal_exist = True
                break
        if not signal_exist:
            async with aiohttp.ClientSession() as session:
                url = host + f'update_signal/{old_signal["ticket"]}'
                data = {'status': False, 'close_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                async with session.patch(url=url, data=data) as resp_patch:
                    await resp_patch.json()
            close_position_signal_list.append(old_signal)

    exist_lieder_signals = new_lieder_signals.copy()  # -----------

    return close_position_signal_list


def close_positions_in_investors(close_position_signal_list):
    if len(close_position_signal_list):  # Закрыть позиции если 'Сопровождать открытие или закрытие'
        for investor in source['investors']:
            init_data, settings, idx = get_investor_data(investor)
            init_mt(init_data=init_data)
            close_investor_positions(close_position_signal_list)

            print(f'\t\t --- [{init_data["login"]}]')
            for _ in close_position_signal_list:
                print(f'\t\t\tзакрытие позиции:', get_investor_position_for_signal(_).comment)


async def execute_lieder(sleep=sleep_update):
    global new_lieder_signals
    url_post = host + 'create_signal'
    while True:
        lieder_positions = get_lieder_positions(lieder_init_data=source['lieder'])
        new_lieder_signals = []

        if lieder_positions:
            try:
                for position in lieder_positions:  # Коллекция существующих сигналов
                    data_json = create_signal_json(position, True)
                    new_lieder_signals.append(data_json)

                for new_signal in new_lieder_signals:  # Отправка сигналов на сервер
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url=url_post, data=new_signal) as resp_post:
                            await resp_post.json()
                            if resp_post.status == 400:  # Если такой сигнал существует, обновить данные
                                url = host + f'update_signal/{new_signal["ticket"]}'
                                data = {'current_price': new_signal['current_price'],
                                        'target_value': new_signal['target_value'],
                                        'stop_value': new_signal['stop_value'],
                                        'profitability': new_signal['profitability']}
                                async with session.patch(url=url, data=data) as resp_patch:
                                    await resp_patch.json()
                signals_exist_event.set()
            except Exception as e:
                print('send_lieder_signals()', e)

        signals_for_close = disable_closed_positions_signals()  # ----------------------------------   Закрытие сигналов
        close_positions_in_investors(signals_for_close)  # -----------------------------------------   Закрытие позиций

        print(
            f'\n\tЛидер [{source["lieder"]["login"]}] {datetime.now().time()} - {len(new_lieder_signals)} сигнал')
        await asyncio.sleep(sleep)


async def execute_investor(investor):
    investor_init_data, investor_settings, investor_id = get_investor_data(investor)
    if not init_mt(init_data=investor_init_data):
        return

    signal_list = synchronize_signal_list(investor, investor_settings)
    #   ---------------------------------------------------------------------------     Открытие
    for signal in signal_list:

        if signal['opening_deal'] in ['Пропуск', 'Не выбрано']:  # Пропустить по настройкам
            continue
        if is_position_opened(signal):  # Пропустить если уже открыта
            continue
        if is_lieder_position_in_investor_history(signal):  # Пропустить если уже была открыта (в истории)
            print(f'\t\tПозиция по сигналу {signal["ticket"]} закрыта ранее инвестором [{investor["login"]}]')
            continue
        if not is_signal_relevance(signal):  # Пропустить если сигнал неактуален
            print(f'\t\tСигнал {signal["ticket"]} неактуален')
            continue
        if not is_symbol_allow(signal['signal_symbol']):    # Пропустить если символ недоступен
            print(f'\t\tСимвол {signal["signal_symbol"]} недоступен')
            continue
        if signal['opening_deal'] == 'Сопровождение' or signal['target_and_stop'] == 'Выставлять':
            tp = get_signal_pips_tp(signal)
            sl = get_signal_pips_sl(signal)
        else:
            tp = sl = 0.0
        volume = .01  # get_lots_for_investment(signal['signal_symbol'], signal['investment'])
        response = open_position(symbol=signal['signal_symbol'], deal_type=signal['deal_type'],
                                 lot=volume, lieder_position_ticket=signal['ticket'], tp=tp, sl=sl)
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
    #   ---------------------------------------------------------------------------     Сопровождение
    for signal in signal_list:

        # Коррекция Тейк-профит и Стоп-лосс
        if signal['opening_deal'] == 'Сопровождение' or signal['target_and_stop'] == 'Выставлять':
            synchronize_position_limits(signal=signal)

    #   ---------------------------------------------------------------------------     Закрытие
    #   -----------------------------------------   Закрытие позиций по инвестору в блоке >> execute_lieder()
    for signal in signal_list:

        if signal['closing_deal'] in ['Пропуск', 'Не выбрано']:  # Пропустить по настройкам
            continue

        if signal['closing_deal'] == 'Закрыть':  # Ручное закрытие через инвест платформу
            position = get_investor_position_for_signal(signal)
            if position:
                close_position(position=position, reason='10')

    print(f'\tИнвестор [{investor["login"]}] {datetime.now().time()} - {len(get_investor_positions())} позиций')


async def task_manager():
    while True:
        await signals_exist_event.wait()

        if len(source['investors']) > 0:
            for _ in source['investors']:
                event_loop.create_task(execute_investor(_))

        signals_exist_event.clear()


if __name__ == '__main__':
    reset_source()
    print(f'\nСистема сигналов [{start_date}]. Обновление Лидера [{source["lieder"]["login"]}] {sleep_update} с.\n')
    event_loop = asyncio.new_event_loop()
    event_loop.create_task(get_settings())
    event_loop.create_task(execute_lieder())
    event_loop.create_task(task_manager())
    event_loop.run_forever()
