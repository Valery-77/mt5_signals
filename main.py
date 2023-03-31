import asyncio

import aiohttp
import requests

from terminal import *

exist_lieder_signals = new_lieder_signals = investor_signals_list = []  # default var
signals_settings = {}  # default var
frontend_signals_settings = {}  # default var
source = {}

sleep_update = 1  # пауза для обновления лидера

host = 'https://my.atimex.io:8000/api/signal/'


async def send_patch(url, data):
    async with aiohttp.ClientSession() as session:
        async with session.patch(url=url, data=data) as response:
            return response


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
            'lieder': {'terminal_path': r'C:\Program Files\MetaTrader 5\terminal64.exe'},
            'investors': [],
            # 'signals': [],
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
                    'opening_deal': source['investors'][idx]['opening_deal'],
                    'closing_deal': source['investors'][idx]['closing_deal'],
                    'target_and_stop': source['investors'][idx]['target_and_stop'],
                    # 'risk': source['investors'][idx]['risk'],
                    'signal_relevance': source['investors'][idx]['signal_relevance']}
        # 'profitability': source['investors'][idx]['profitability'],
        # 'profit': source['investors'][idx]['profit']}
        return init_data, settings, idx


def create_position_signal_json(lieder_balance, lieder_position):
    #   расчет плеча сделки лидера
    contract_size = Mt.symbol_info(lieder_position.symbol).trade_contract_size
    if contract_size and lieder_balance > 0:
        leverage = (contract_size * lieder_position.volume * lieder_position.price_open) / lieder_balance
    else:
        leverage = 0
    #   тело запроса
    return {'ticket': lieder_position.ticket,
            'deal_type': lieder_position.type,
            'current_price': lieder_position.price_current,
            'deal_leverage': leverage,
            'signal_symbol': lieder_position.symbol,
            'open_price': lieder_position.price_open,
            'target_value': lieder_position.tp,
            'stop_value': lieder_position.sl,
            'status': True, }
    # 'profitability': lieder_position.profit,
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
    global signals_settings, source, frontend_signals_settings
    url = host + 'setting/last'
    while True:
        # print('\t----', datetime.now())
        try:
            response = requests.get(url=url).json()
            # async with aiohttp.ClientSession() as session:
            #     async with session.get(url) as get_response:
            #         print(url)
            #         response = await get_response.json()
        except Exception as e:
            print(e)
            response = {}

        if len(response):
            reset_source(only_investors=True)
            signals_settings = response[0]
            # print(signals_settings)
            # source['settings_id'] = signals_settings['id']
            source['lieder'] = {'login': int(signals_settings['leader_login']),
                                'password': signals_settings['leader_password'],
                                'server': signals_settings['leader_server'],
                                'terminal_path': r'C:\Program Files\MetaTrader 5\terminal64.exe'}
            multiply = signals_settings['multiplier']
            multiplier = float(multiply) if multiply else 1
            rlv = signals_settings['signal_relevance']
            relevance = float(rlv) if rlv else 1
            investor_data_first = {'login': int(signals_settings['investor_login_1']),
                                   'password': signals_settings['investor_password_1'],
                                   'server': signals_settings['investor_server_1'],
                                   'investment': float(signals_settings['investment_1']),
                                   'multiplier': multiplier,
                                   'opening_deal': signals_settings['opening_deal'],
                                   'closing_deal': signals_settings['closing_deal'],
                                   'target_and_stop': signals_settings['target_and_stop'],
                                   # 'profitability': float(signals_settings['profitability']),
                                   # 'risk': float(signals_settings['risk']),
                                   # 'profit': float(signals_settings['profit']),
                                   'signal_relevance': relevance}

            source['investors'].append(investor_data_first)

            frontend_signals_settings = source['investors'][-1]

            if signals_settings['investor_login_2'] and signals_settings['investor_password_2'] and signals_settings['investor_server_2']:
                investor_data_second = investor_data_first.copy()
                investor_data_second['login'] = int(signals_settings['investor_login_2'])
                investor_data_second['password'] = signals_settings['investor_password_2']
                investor_data_second['server'] = signals_settings['investor_server_2']
                investor_data_second['investment'] = float(signals_settings['investment_2'])
                source['investors'].append(investor_data_second)
        else:
            reset_source()
        await asyncio.sleep(sleep)


async def get_signals_list(sleep=sleep_update):
    global signals_settings, investor_signals_list
    url = host + 'active'
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as get_response:
                    if get_response:
                        # print(get_response)
                        response = await get_response.json()
        except Exception as e:
            print(e)
            response = {}
        investor_signals_list = []
        if len(response):
            for signal in response:
                investor_signals_list.append(signal)
        await investors_executor()
        await asyncio.sleep(sleep)


def unite_signals_list(signals_list, signal_settings):
    united_signals = []
    for signal_ in signals_list:
        signal = signal_.copy()
        signal.update(signal_settings)  # сложить данные о сигнале лидера и настроек сигнала инвестора
        united_signals.append(signal)
    return united_signals


async def disable_closed_positions_signals():
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
            try:
                url = host + f'update/ticket/{old_signal["ticket"]}'
                data = {'status': False, 'close_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                async with aiohttp.ClientSession() as session:
                    async with session.patch(url=url, data=data) as resp_patch:
                        await resp_patch.json()
                close_position_signal_list.append(old_signal)
            except Exception as e:
                print(e)

    exist_lieder_signals = new_lieder_signals.copy()  # -----------

    return close_position_signal_list


async def execute_lieder(sleep=sleep_update):
    global new_lieder_signals
    url_post = host + 'create'  # 'create_signal'
    while True:
        if len(source['lieder']) < 2:
            await asyncio.sleep(sleep)
            continue
        lieder_positions = get_lieder_positions(lieder_init_data=source['lieder'])
        new_lieder_signals = []

        if lieder_positions:
            try:
                balance = Mt.account_info().balance
                for position in lieder_positions:  # Коллекция существующих сигналов
                    data_json = create_position_signal_json(balance, position)
                    new_lieder_signals.append(data_json)
                for new_signal in new_lieder_signals:  # Отправка сигналов на сервер
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url=url_post, data=new_signal) as resp_post:
                            await resp_post.json()
                            if resp_post.status == 400:  # Если такой сигнал существует, обновить данные
                                url = host + f'update/ticket/{new_signal["ticket"]}'  # f'update_signal/{new_signal["ticket"]}'
                                data = {'current_price': new_signal['current_price'],
                                        'target_value': new_signal['target_value'],
                                        'stop_value': new_signal['stop_value'], }
                                async with session.patch(url=url, data=data) as resp_patch:
                                    await resp_patch.json()
            except Exception as e:
                print('execute_lieder()', e)

        await disable_closed_positions_signals()  # ----------------------------   Закрытие сигналов
        if source["lieder"]["login"]:
            print(
                f'\n\tЛидер [{source["lieder"]["login"]}] {datetime.now().time()} - {len(new_lieder_signals)} сигнал')

        # for signal in investor_signals_list:
        #     deal_type = 'BUY' if signal['deal_type'] == 0 else 'SELL'
        #     await send_comment(f'{signal["signal_symbol"]}  {deal_type}  Плечо:{signal["deal_leverage"]}')

        await asyncio.sleep(sleep)


async def send_comment(comment_text):
    print(f'\t\t --- {comment_text}')
    async with aiohttp.ClientSession() as session:
        async with session.get(url=host + 'setting/last') as response:
            idx = await response.json()
    url = host + f'setting/update/{idx[0]["id"]}'
    data = {'comment': comment_text}
    async with aiohttp.ClientSession() as session:
        async with session.patch(url=url, data=data) as response:
            return response


async def execute_investor(investor, new_signals_list):

    investor_init_data, settings_signal, investor_id = get_investor_data(investor)
    if not init_mt(init_data=investor_init_data):
        await send_comment(f'Ошибка инициализации {investor["login"]}')
        return

    print(f'\tИнвестор [{investor["login"]}] {datetime.now().time()} - {len(get_investor_positions())} позиций')
    #   ---------------------------------------------------------------------------     Объединение сигналов и настроек
    signal_list = unite_signals_list(new_signals_list, settings_signal)
    #   ---------------------------------------------------------------------------     Вывод Доходность, Риск, Профит
    for _ in signal_list:
        url_db = host + f'update/ticket/{_["ticket"]}'
        data = {'profitability': str(get_profitability(_)),
                'profit': str(get_profit(_)),
                'risk': str(get_risk(_))}
        await send_patch(url=url_db, data=data)
    #   ---------------------------------------------------------------------------     Закрытие позиций по Сопровождению
    init_mt(init_data=investor_init_data)
    exist_positions = get_investor_positions()
    for e_pos in exist_positions:
        comment = DealComment().set_from_string(e_pos.comment)
        position_exist = False
        for signal in signal_list:
            # if signal['closing_deal'] != 'escort':  # 'Сопровождение':
            #     continue
            if signal['ticket'] == comment.lieder_ticket:
                position_exist = True
                break
        if (frontend_signals_settings['closing_deal'] == 'escort'
            or frontend_signals_settings['opening_deal'] == 'escort') \
                and not position_exist:
            close_position(investor=investor, position=e_pos, reason='003')
            await send_comment(f'\t --- {e_pos.ticket} {reasons_code["003"]}')
    #   ---------------------------------------------------------------------------     Открытие
    init_mt(init_data=investor_init_data)
    for signal in signal_list:

        if signal['opening_deal'] not in ['escort', 'open']:  # Пропустить по настройкам
            continue
        if not is_symbol_allow(signal['signal_symbol']):  # Пропустить если символ недоступен
            print(f'\t\tСимвол {signal["signal_symbol"]} недоступен')
            continue
        if is_position_opened(signal):  # Пропустить если уже открыта
            continue
        if is_lieder_position_in_investor_history(signal):  # Пропустить если уже была открыта (в истории)
            print(f'\t\tПозиция по сигналу {signal["ticket"]} закрыта ранее инвестором [{investor["login"]}]')
            continue
        if not is_signal_relevance(signal):  # Пропустить если сигнал неактуален
            await send_comment(f'Сигнал {signal["ticket"]} неактуален')
            continue
        if signal['opening_deal'] == 'escort' or signal['target_and_stop'] == 'set':
            tp = get_signal_pips_tp(signal)
            sl = get_signal_pips_sl(signal)
        else:
            tp = sl = 0.0
        volume = get_deal_volume(signal)
        init_mt(init_data=investor_init_data)
        response = open_position(symbol=signal['signal_symbol'], deal_type=signal['deal_type'],
                                 lot=volume, lieder_position_ticket=signal['ticket'], tp=tp, sl=sl)
        if response:
            try:
                ret_code = response.retcode
                lots = response.volume
            except AttributeError:
                ret_code = response['retcode']
                lots = 0
            if ret_code:
                deal_type = 'BUY' if signal['deal_type'] == 0 else 'SELL'
                # await send_comment(f'{signal["signal_symbol"]} {deal_type} lot:{lots} lev:{signal["deal_leverage"]}')
                msg = f'\t --- [{investor["login"]}] {deal_type} {send_retcodes[ret_code][1]}:{ret_code} : сигнал {signal["ticket"]}'
                print(msg)
        else:
            print('EMPTY_OPEN_DEAL_RESPONSE')
    #   ---------------------------------------------------------------------------     Сопровождение
    if not len(get_investor_positions()):
        return

    init_mt(init_data=investor_init_data)
    for signal in signal_list:
        # Коррекция Тейк-профит и Стоп-лосс
        if signal['opening_deal'] == 'escort' or signal['target_and_stop'] == 'set':
            synchronize_position_limits(signal=signal)

    #   ---------------------------------------------------------------------------     Закрытие
    init_mt(init_data=investor_init_data)
    for signal in signal_list:
        if signal['closing_deal'] == 'close':  # Ручное закрытие через инвест платформу
            close_signal_position(signal=signal, reason='002')
            await send_comment(f'\t --- {signal["ticket"]} {reasons_code["002"]}')
            # position = get_investor_position_for_signal(signal)
            # if position:
            #     close_position(investor=investor, position=position, reason='002')


async def investors_executor():
    if len(source['investors']):
        for _ in source['investors']:
            await execute_investor(_, investor_signals_list)


if __name__ == '__main__':
    reset_source()
    # print(f'\nСистема сигналов [{start_date}]. Обновление Лидера [{source["lieder"]["login"]}] {sleep_update} с.\n')
    event_loop = asyncio.new_event_loop()
    event_loop.create_task(get_settings())
    event_loop.create_task(execute_lieder())
    event_loop.create_task(get_signals_list())
    event_loop.run_forever()
