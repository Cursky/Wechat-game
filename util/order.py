global key
key = None


async def run_order(order, conversation, self, value_dict):
    global key

    # 解锁 e.g: unlock_123 使用123为key解锁
    if "unlock_" in order:
        if key == order.split("unlock_")[1]:
            key = None

    # 带锁时仅允许unlock指令，其余return
    if key is not None:
        return

    # 上锁 e.g: lock_123 使用123为key进行上锁 上锁后需要使用unlock否则指令失效
    if "lock_" in order and "unlock_" not in order:
        key = order.split("lock_")[1]

    # out指令， 快捷退出，是的，我使用ctrl+c非常的慢
    if order == "out":
        exit("using out order")

    if order == "print_value_dict":
        await conversation.say(f"{value_dict}")

    # init_check 初始化检查，允许对配置进行检查，也有预先加载的作用
    # 不预先加载 将会在第一次使用其函数时触发加载 预先加载不是必须的但能提前发现问题
    if order == "init_check":
        await self.get_bot_room()
        await self.get_player_room()

    return
