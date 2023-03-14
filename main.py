import asyncio
import aiohttp
from datetime import datetime, timedelta
from terminal import init_mt

SERVER_DELTA_TIME = timedelta(hours=4)
start_date = datetime.now().replace(microsecond=0)
trading_event = asyncio.Event()  # init async event
lieder_positions = []  # default var
signals_settings = {}  # default var

sleep_update = 3  # пауза для обновления лидера

host = 'http://127.0.0.1:8000/api/'

# def set_dummy_data():
#     global start_date
#     investment_size = 1000
#     source['lieder'] = {
#         'terminal_path': r'C:\Program Files\MetaTrader 5\terminal64.exe',
#         'login': 66587203,
#         'password': '3hksvtko',
#         'server': 'MetaQuotes-Demo'
#     }
#     source['investors'] = [
#         {
#             'terminal_path': r'C:\Program Files\MetaTrader 5_2\terminal64.exe',
#             'login': 65766034,
#             'password': 'h0nmgczo',
#             'server': 'MetaQuotes-Demo',
#             'investment_size': investment_size,
#             'dcs_access': True,
#
#             'deal_in_plus': 0.1,
#             'deal_in_minus': -0.1,
#             'waiting_time': 1,
#             'ask_an_investor': 'Все',
#             'price_refund': 'Да',
#             # -----------------------------------------
#             'multiplier': 'Баланс',
#             'multiplier_value': 100.0,
#             'changing_multiplier': 'Да',
#             # -----------------------------------------
#             'stop_loss': 'Процент',
#             'stop_value': 20.0,
#             'open_trades': 'Закрыть',
#             # -----------------------------------------
#             'shutdown_initiator': 'Инвестор',
#             'disconnect': 'Нет',
#             'open_trades_disconnect': 'Закрыть',
#             'notification': 'Нет',
#             'blacklist': 'Нет',
#             'accompany_transactions': 'Нет',
#             # -----------------------------------------=
#             'no_exchange_connection': 'Нет',
#             'api_key_expired': 'Нет',
#             # -----------------------------------------
#             'closed_deals_myself': 'Переоткрывать',
#             'reconnected': 'Переоткрывать',
#             # -----------------------------------------
#             'recovery_model': 'Не корректировать',
#             'buy_hold_model': 'Не корректировать',
#             # -----------------------------------------
#             'not_enough_margin': 'Минимальный объем',
#             'accounts_in_diff_curr': 'Доллары',
#             # -----------------------------------------
#             'synchronize_deals': 'Нет',
#             'deals_not_opened': 'Нет',
#             'closed_deal_investor': 'Нет',
#             # -----------------------------------------
#         }
#     ]
#     source['investors'].append(source['investors'][0].copy())
#     source['investors'][1]['terminal_path'] = r'C:\Program Files\MetaTrader 5_3\terminal64.exe'
#     source['investors'][1]['login'] = 5009600048
#     source['investors'][1]['password'] = 'sbbsapv5'
#     source['settings'] = {
#         "relevance": True,
#         "update_at": str(start_date),
#         "create_at": str(start_date)
#         # "access": response['access'],
#     }


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
        print(signals_settings)
        await asyncio.sleep(sleep)


async def update_lieder_info(sleep=sleep_update):
    global lieder_positions
    while True:
        # if len(source) > 0:
        #     init_res = init_mt(init_data=source['lieder'])
        #     if not init_res:
        #         await asyncio.sleep(sleep)
        #         continue
        #     lieder_positions = Mt.positions_get()
        #     print(
        #         f'\nLIEDER {source["lieder"]["login"]} [{source["lieder"]["currency"]}] - {len(lieder_positions)} positions :',
        #         datetime.utcnow().replace(microsecond=0))
        #     trading_event.set()
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

        # if len(source) > 0:
        #     for _ in source['investors']:
        #         event_loop.create_task(execute_investor(_))

        trading_event.clear()


if __name__ == '__main__':
    # set_dummy_data()
    event_loop = asyncio.new_event_loop()
    # event_loop.create_task(update_setup())  # для теста без сервера закомментировать
    event_loop.create_task(get_settings())

    # event_loop.create_task(update_lieder_info())
    # event_loop.create_task(task_manager())
    event_loop.run_forever()
