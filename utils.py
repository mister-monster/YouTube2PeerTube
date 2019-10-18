import toml

def read_conf(conf_file):
    conf_file = open(conf_file)
    conf = conf_file.read()
    conf = toml.loads(conf)
    conf_file.close()
    return conf

def convert_timestamp(timestamp):
    timestamp = timestamp.split('T')
    date = timestamp[0].split('-')
    time = timestamp[1].split('+')
    time = time[0].split(':')
    timestamp = int(date[0] + date[1] + date[2] + time[0] + time[1] + time[2])
    return timestamp
