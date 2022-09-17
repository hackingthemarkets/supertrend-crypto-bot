
def trade_log(message, filepath='log/trade_log.txt', log=False):
    if log:
        print(message, end='')
        file = open(filepath, 'a')
        file.write(message)
        file.close()