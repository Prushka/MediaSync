import redis

r = redis.Redis(host='cloud.muddy.ca', port=6399, db=0, password="vWw@U4mzCw2am02iDFYp")
rp = r.pubsub()

def my_handler(message):
    print('MY HANDLER: ', str(message['data'].decode("utf-8")))


def subscribe():
    p = r.pubsub()
    p.subscribe(**{'saine': my_handler})
    thread = p.run_in_thread(sleep_time=0.001)


def flush():
    r.flushall()


if __name__ == '__main__':
    subscribe()

    while True:
        x = input()
        r.publish("saine", x)
        print(f"Published: {x}")
