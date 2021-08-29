import paddlehub as hub


# 他需要 paddlepaddle
class Nlp:

    def __init__(self, use_gpu=False):
        # 用于分词
        self.lac = hub.Module(name="lac")
        # 用于语义相似度
        self.simnet_bow = hub.Module(name="simnet_bow")
        # 用于情感分类（正负）
        self.senta = hub.Module(name="senta_bilstm")
        self.use_gpu = use_gpu

        self.__temp_dict = {"text": None}

    def cut(self, word):
        """
        分词
        :param word: str or list
        :return:
        """
        return self.lac.cut(text=[word], use_gpu=self.use_gpu, batch_size=1, return_tag=True)

    def sentiment_classify(self, word):
        """
        情感分类
        :param word:
        :return:
        """
        if isinstance(word, str):
            word = [word]
        self.__temp_dict['text'] = word

        return self.senta.sentiment_classify(data=self.__temp_dict, use_gpu=self.use_gpu)

    def is_positive(self, word):
        return bool(self.sentiment_classify(word)[0]['sentiment_label'])

    def similarity(self, word1, word2):
        """
        语义相似度

        word1 和 word2 的数目应当是对齐的
        例如 ["ding", "ding","ding",]
        与  ["hi", "hi","hi",]

        :param word1: str or list
        :param word2:
        :return:
        """
        if isinstance(word1, str):
            word1 = [word1]
        if isinstance(word2, str):
            word2 = [word2]

        assert word1.__len__() == word2.__len__(), "word1 和 word2 的数目需要相同"

        return self.simnet_bow.similarity(texts=[word1, word2], use_gpu=self.use_gpu)

    def get_name(self, name) -> str or None:
        """
        优先'PER'，后'nz'
        最后没有，就None
        :param name:
        :return:
        """
        result = self.cut(name)[0]
        if 'PER' in result['tag']:
            return result['word'][result['tag'].index('PER')]

        if 'nz' in result['tag']:
            return result['word'][result['tag'].index('nz')]

        return None

    def most_similarity(self, word: str, word_list: list, threshold: float=None):
        """
        word_list中找与word最相似的

        :param word:
        :param word_list:
        :param threshold: 为None意味着不进行阈值筛选，仅选择最大相似度的
        存在值意味着最大相似度不超过阈值，那么返回None
        :return:
        """
        if isinstance(word, str):
            word = [word] * word_list.__len__()

        result = self.similarity(word, word_list)

        result = sorted(result, key=lambda x: x['similarity'])[-1]

        if threshold is None or result['similarity'] >= threshold:
            return result['text_2']


if __name__ == '__main__':
    nlp = Nlp()

    print(nlp.sentiment_classify("你妈的个比"))
    print(type(nlp.get_name("我是陈晨指挥官")))
    print(nlp.most_similarity("让他们回来吧", ["继续前进", '返航回来'], threshold=None))
