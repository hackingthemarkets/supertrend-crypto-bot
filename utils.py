# def record_state(is_in_position, position):
#     file = open('log/state.txt', 'w')
#     file.write(f"{is_in_position},{position}")
#     file.close()

def trade_log(message):
    print(message, end='')
    file = open('log/trade_log.txt', 'a')
    file.write(message)
    file.close()