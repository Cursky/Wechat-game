import asyncio
from wechaty import Wechaty, Contact, RoomQueryFilter
from wechaty.user import Message, Room
from wechaty_puppet import FileBox, ScanStatus
from typing import Optional, Union
import os
import logging
import random
import argparse

# 导入配置和剧情
from configs import *
from util import run_order, Nlp


bot_name = "AEEIS"
value_dict['bot_list'].append(bot_name)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.ERROR)


class AEEIS(Wechaty):

    def __init__(self):
        super().__init__()
        self.bot_room = None
        self.player_room = None
        self.player = None

        self.nlp = Nlp()
        self.plot_loader = PlotLoader()

        self.sequence: int = 0

        self.start_flag: bool = True
        self.wait_flag: bool = True
        self.is_start_scene: bool = True

    # async def on_ready(self, payload):
    #     # 我不知道为什么，但是他始终无法触发on_ready,或许需要第一次登录？

    async def find_room(self, topic: str):
        """
        通过 名字 获取bot_room
        如果未找到！ 抛出错误并结束程序

        :param topic:  room名
        :return:
        """
        room = await self.Room.find(query=RoomQueryFilter(topic=topic))

        if room is None:
            error = f"没能找到{room}room, 请检查配置"
            log.error(error)
            exit(error)

        return room

    async def get_bot_room(self):
        """
        获取bot_room
        如果bot_room已被获取一次，将直接返回
        如果未找到！ 抛出错误并结束程序
        :return:
        """
        if self.bot_room is None:
            bot_room = await self.find_room(value_dict['bot_room'])
            self.bot_room = bot_room
        return self.bot_room

    async def get_player_room(self):
        """
        同上 get_bot_room
        :return:
        """
        if self.player_room is None:
            player_room = await self.find_room(value_dict['player_room'])
            self.player_room = player_room
        return self.player_room

    async def on_login(self, contact: Contact):
        print(f'user: {contact} has login')

    async def on_scan(self, status: ScanStatus, qr_code: Optional[str] = None, data: Optional[str] = None):

        contact = self.Contact.load(self.contact_id)
        print(f'user <{contact}> scan status: {status.name} , '
              f'qr_code: {qr_code}')

    @staticmethod
    def render(render_str, render_dict, render_flag='$', define_render=''):
        """
        变量渲染
        :param render_str: 需要渲染的字符串
        :param render_dict: 存放相应变量的字典
        如果字典中不存在对应变量，将渲染默认值define_render
        :param render_flag: 分隔符
        :param define_render: 渲染默认值
        :return:
        """
        split_list = render_str.split(render_flag)
        split_len = split_list.__len__()

        if split_len % 2 == 1 and split_len >= 3:
            # 存在需要渲染的变量
            for i in range(1, split_len, 2):
                render_str = render_str.replace(
                    f"{render_flag}{split_list[i]}{render_flag}",
                    f"{render_dict.get(split_list[i], define_render)}"
                )

        return render_str

    async def plot_say(self, say_tuple, render_dict, delay=0.7, delay_word_num=15):
        """
        剧情说话
        采用("发送方法", "话语")的约定格式
        并且渲染其中变量
        并且根据字数设置延时
        :param say_tuple: ("发送方法", "话语")
        :param render_dict: 渲染字典，详情看渲染函数
        :param delay: 延时基础时常
        :param delay_word_num: 每多少长度 延时多少基础时常
            注： 公式为 word_num / delay_word_num 的和 * delay
        :return:
        """
        say_str = self.render(say_tuple[1], render_dict)

        if say_tuple[0] == "talker":
            await self.player.say(say_str)
        if say_tuple[0] == "room":
            player_room = await self.get_player_room()
            await player_room.say(say_str)

        if delay is not None:
            await asyncio.sleep((say_str.__len__() / delay_word_num) * 0.7)

    async def spokesman_speaks(self, say_dict, text, render_dict):
        """
        发言人顺序讲话
        每当获取到一次能够传入的text(逻辑应当提前想好)
        将会通过self.sequence顺序（下标作用）确定当前发言人
            1. 如果发言人是自己，那么根据say_dict中定义的say_tuple来选
                择合适的发言，并且会完成字符串的渲染，发送后移动下标sequence顺序
            注：say_tuple的格式关注plot_say函数注释
            2. 如果发言人不是自己，那么判断当前发言人是谁（使用约定的格式获取）
            如果当前text发言人是say_dict中的当前发言人（一致）那么下标前进
            否则跳过并等待下次调用
            注： 使用约定的格式获取为  bot_name:say_tuple, 并且理论只能在bot_room中
                获取到

        :param say_dict:say_dict 约定好的 plot故事中剧情的格式
            它是dict，且由带顺序的dict组成，其中key是发言人，value是say_tuple
            e.g: {
                "AEEIS_0":("room","聊天室发话")，
                AEEIS_1":("talker,"私聊发话")
            }
        :param text: 当前别人说的话，应当符合约定的格式bot_name:say_tuple
        :param render_dict: 渲染列表
        :return:
        """
        # 通过顺序下标得到当前剧情发言人
        bot_room = await self.get_bot_room()
        if say_dict.__len__() == 0:
            await bot_room.say(f"{bot_name}:None")
            return

        spokesman = tuple(say_dict.keys())[self.sequence]

        if bot_name in spokesman:
            # 是自己发言，开始将话
            say_tuple = say_dict[spokesman]

            if say_tuple is not None:
                await self.plot_say(say_tuple, render_dict)

            # 并且在bot_room中发话，发送符合约定的格式
            await bot_room.say(f"{bot_name}:{say_tuple}")

        else:
            # 非自己发言，那么说明现在在等待一个人发言，判断此次发言是否是目标人物
            # 诺不是就直接返回，sequence不变
            # 这是为了未来多机器人准备
            if text.split(':')[0] not in spokesman:
                return

        self.sequence += 1

    async def start_scene(self, text):
        say_dict = self.plot_loader.running_plot[1]

        await self.spokesman_speaks(say_dict, text, value_dict)

        # 如果下标超过
        if self.sequence > say_dict.__len__() - 1 or say_dict.__len__() == 0:
            # 超过了say_dict的下标，说明已经结束了
            self.sequence = 0
            self.is_start_scene = False

    async def end_scene(self, text):
        info_dict = self.plot_loader.running_plot[2]
        flag_dict = info_dict[f"{bot_name}_return"]

        dict_key = flag_dict[None] if flag_dict.__len__() == 1 else \
            flag_dict[self.nlp.most_similarity(text, list(flag_dict.keys()), threshold=None)]

        say_dict = info_dict[dict_key]

        await self.spokesman_speaks(say_dict, text, value_dict)

        # 如果下标超过
        if self.sequence > say_dict.__len__() - 1 or say_dict.__len__() == 0:
            # 超过了say_dict的下标，说明已经结束了
            self.sequence = 0
            self.is_start_scene = True
            self.wait_flag = True
            temp_dict = info_dict[f'{dict_key}_over']
            value_dict["next_goto"] = tuple(map(int, temp_dict['next_goto'].split()))
            value_dict["reason_and_sensibility"][0] = \
                value_dict["reason_and_sensibility"][0] + int(temp_dict["reason"])
            value_dict["reason_and_sensibility"][1] = \
                value_dict["reason_and_sensibility"][1] + int(temp_dict["sensibility"])
            self.plot_loader.running_plot = self.plot_loader.load_plot(value_dict["next_goto"])

    async def on_message(self, msg: Message):
        # 判断是否是在room中，并且使用conversation统一
        conversation, is_room = (msg.talker(), False) if msg.room() is None else (msg.room(), True)

        # 此段代码可读性不高，他的本质是保证仅通过botroom进行说话顺序和剧情推进
        # 所以此段逻辑为 他除了来自botroom的消息他全部接受（包括自己），其余的只接受玩家私聊
        if is_room is True:
            topic = await conversation.topic()
            # 是bot房的，无论是不是自己都接受
            if topic != value_dict['bot_room']:
                # 不是bot房，由于
                # AEEIS是特殊的，他只通过私聊获取指令，指挥官也仅有向AEEIS下达指令的能力
                # 如果在room中获取的消息，丢弃
                return
        elif msg.is_self():
            # 在私聊，但不接受自己的话
            return

        # 文本内容
        text = msg.text()

        await conversation.ready()

        # 允许使用指令进行操控, 详情看order.py (属于util)
        if "#指令#" in text:
            order = text.split()
            if order.__len__() != 3 or order[1] != bot_name:
                return

            await run_order(order[2], conversation, self, value_dict)
            return

        if self.player is None:
            self.player = conversation

        if self.player != conversation:
            # 如果是非用户输入，说明在演绎剧情
            if self.is_start_scene:
                # 演绎开始剧情
                await self.start_scene(text)
                return

            if not self.wait_flag:
                # 说明用户已经输入，开始演绎
                await self.end_scene(text)
                return

            # 那么此刻是开始剧情演绎完后，导致的
            # 过滤此次即可
            return

        # 下面是用户输入，判断如果是还没开启
        if self.start_flag:
            # 如果是还未开启，则启动剧情演绎
            self.start_flag = False
            # 只启动一次

            await self.start_scene(text)

        if not self.is_start_scene:
            # 如果不是在开头演绎剧情那么是用户的回答

            # 是可以设置特殊剧情的，这个给个例子
            if value_dict['plot_points'] == (0, 0, 0):

                name = self.nlp.get_name(text)

                # 和用户开个玩笑
                temp_dict = self.nlp.sentiment_classify(text)[0]

                if name is None or (temp_dict['sentiment_label'] == 0 and temp_dict['negative_probs'] >= 0.90):
                    name = f"{random.randint(12342, 12341314)}号"

                    await conversation.say(
                        f"你可以浪费很多时间在无意义的发泄上，但按照条例，刚刚是你唯一向我说明昵称的机会。"
                    )

                    await conversation.say(
                        f"也许你现在很愤怒, 但你浪费的每一秒钟，都让人类胜利的可能性又降低了一分。"
                    )

                    value_dict['reason_and_sensibility'][1] += 1

                value_dict['name'] = name

            self.wait_flag = False
            await self.end_scene(text)

            # 处理后选择分支并启动其余对话
            return


async def main(args):
    os.environ['WECHATY_PUPPET'] = "wechaty-puppet-service"
    os.environ['WECHATY_PUPPET_SERVICE_TOKEN'] = args.token

    bot = AEEIS()

    await bot.start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--token', required=True, type=str, help='your WECHATY_PUPPET_SERVICE_TOKEN')
    args = parser.parse_args()

    asyncio.run(main(args))

