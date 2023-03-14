import asyncio
import aiohttp
from terminal import *

trading_event = asyncio.Event()  # init async event
lieder_positions = []  # default var
signals_settings = {}  # default var
lieder_setup = {
    'terminal_path': r'C:\Program Files\MetaTrader 5\terminal64.exe',
    'login': 66587203,
    'password': '3hksvtko',
    'server': 'MetaQuotes-Demo'
}

sleep_update = 3  # пауза для обновления лидера

host = 'http://127.0.0.1:8000/api/'


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
        # print(signals_settings)
        if len(response) > 0:
            investor_data = {'login': response[0]['investor_login_1'],
                             'password': response[0]['investor_password_1'],
                             'server': response[0]['investor_server_1'],
                             'investment': response[0]['investment_1'],
                             'multiplier': response[0]['multiplier'],
                             'state': response[0]['state'],
                             'target_value': response[0]['target_value'],
                             'stop_value': response[0]['stop_value'],
                             'opening_deal': response[0]['opening_deal'],
                             'closing_deal': response[0]['closing_deal'],
                             'target_and_stop': response[0]['target_and_stop'],
                             'profitability': response[0]['profitability'],
                             'risk': response[0]['risk'],
                             'profit': response[0]['profit']}
            source['investors'].append(investor_data)
            investor_data_second = investor_data.copy()
            investor_data_second['login'] = response[0]['investor_login_2']
            investor_data_second['password'] = response[0]['investor_password_2']
            investor_data_second['server'] = response[0]['investor_server_2']
            investor_data_second['investment'] = response[0]['investment_2']
            source['investors'].append(investor_data_second)
        await asyncio.sleep(sleep)


async def update_lieder_info(sleep=sleep_update):
    global lieder_positions
    while True:
        lid_positions = get_lieder_positions(lieder_data=lieder_setup)
        lieder_positions = lid_positions
        if lid_positions:
            for position in lid_positions:
                url = host + 'create_signal'
                data_json = create_signal_json(position, True)
                async with aiohttp.ClientSession() as session:
                    async with session.post(url=url, data=data_json) as resp_post:
                        response = await resp_post.json()
                        if resp_post.status == 400:
                            url = host + f'update_signal/{data_json["ticket"]}'
                            data = {'current_price': data_json['current_price'],
                                    'profitability': data_json['profitability']}
                            async with session.patch(url=url, data=data) as resp_patch:
                                response = await resp_patch.json()
                        # print(response)
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
        close_positions_by_lieder(investor, lieder_positions)

    # Mt.shutdown()


async def task_manager():
    while True:
        await trading_event.wait()

        # if len(source) > 0:
        #     for _ in source['investors']:
        #         event_loop.create_task(execute_investor(_))

        trading_event.clear()


if __name__ == '__main__':
    event_loop = asyncio.new_event_loop()
    event_loop.create_task(get_settings())
    event_loop.create_task(update_lieder_info())
    # event_loop.create_task(task_manager())
    event_loop.run_forever()
