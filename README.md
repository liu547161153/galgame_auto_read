# galgame_auto_read
一个能自动阅读galgame文本的小工具，调用voicevox api(我没有python基础，所有代码都是ChatGPT敲的)

此工具会监听剪贴板并自动阅读内容（仅限日文），所以还需要一个能提取游戏文本到剪贴板的工具，vnr或者LunaTranslator之类的，该软件用到了分析文本中情绪表达的模型

使用方法是python设置好后，先安装运行环境，再运行main.py即可,输入要转换语音的人名和voicevox的speakerID,选择旁白的ID，按确定将开始监听，取消键可以结束监听（记得运行前打开voicevox）

还有音频通道是voicevox将要输出的设备，你必须使用虚拟麦克风VBCABLE，然后用Voicemeeter Banana把VBCABLE的音量拉高，怎么配置这两个软件请参考：https://www.bilibili.com/read/cv12412936/

![C2}KWX$_%F1`Z4{7XAM9KQ5](https://user-images.githubusercontent.com/18525855/231684017-35cb5c51-a4a5-4ef7-b186-e97682bd00a8.png)
