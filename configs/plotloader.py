from .plot import *


class PlotLoader(object):

    def __init__(self, points=value_dict['next_goto']):
        self.running_plot = self.load_plot(points)

    @staticmethod
    def is_accord(requirement, condition=value_dict['reason_and_sensibility']):
        # [（理性大于0， 理性小于等于0)， (感性大于0，感性小于等于0）, 他们之间的比值, 为None不比]
        # reason_and_sensibility (理性， 感性)
        # 可读性较差，建议不细看
        if requirement[0][0] <= condition[0] <= requirement[0][1] and requirement[1][0] <= condition[1] <= \
                requirement[1][1]:
            if requirement[2] is None or abs(condition[0] / (condition[1] + 0.0001) - requirement[2]) <= 0.05:
                return True
        return False

    def load_plot(self, points=value_dict['next_goto']):
        try:
            # level, chapters, scene = points
            story = plot[points[0]][points[1]]

            if not self.is_accord(story['条件']):
                #     raise AssertionError(f"""
                #     剧情 chapters 条件不符合, 目前剧情点 {value_dict['plot_points']} 期望前往剧情点 {value_dict['next_goto']}
                #     但不满足 第{points[0]}关 第{points[1]}剧情 条件：{story['条件']}
                #     目前的 reason_and_sensibility 为 {value_dict['reason_and_sensibility']}
                # """)
                #     exit("剧情 chapters 条件不符合")
                exit(f"""
                    剧情 chapters 条件不符合, 目前剧情点 {value_dict['plot_points']} 期望前往剧情点 {value_dict['next_goto']}
                    但不满足 第{points[0]}关 第{points[1]}剧情 条件：{story['条件']}
                    目前的 reason_and_sensibility 为 {value_dict['reason_and_sensibility']}
                """)

            if not self.is_accord(story['流程'][points[2]][0]['条件']):
                #     raise AssertionError(f"""
                #     幕 scene 条件不符合, 目前剧情点 {value_dict['plot_points']} 期望前往剧情点 {value_dict['next_goto']}
                #     但不满足 第{points[0]}关 第{points[1]}剧情 第{points[2]}幕 条件：{story['条件']}
                #     目前的 reason_and_sensibility 为 {value_dict['reason_and_sensibility']}
                # """)
                #     exit("幕 scene 条件不符合")
                exit(f"""
                    幕 scene 条件不符合, 目前剧情点 {value_dict['plot_points']} 期望前往剧情点 {value_dict['next_goto']}
                    但不满足 第{points[0]}关 第{points[1]}剧情 第{points[2]}幕 条件：{story['条件']}
                    目前的 reason_and_sensibility 为 {value_dict['reason_and_sensibility']}
                """)

            value_dict['plot_points'] = points
            return story['流程'][points[2]]
        except Exception as err:
            exit(f"""
                    错误信息 {err},
                    目前剧情点 {value_dict['plot_points']} 期望前往剧情点 {value_dict['next_goto']}
                """)

    # def is_start_scene(self):
    #     return value_dict['plot_points'] == self.running_plot[0]['plot_points']


if __name__ == '__main__':
    loader = PlotLoader()
    print(loader.load_plot((0,0,1)))
