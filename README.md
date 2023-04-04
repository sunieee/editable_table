# 自动Docker拉取

见：https://vsde0sjona.feishu.cn/wiki/wikcnIapLeHwhmiQYrZYQZ9KySb

用python写一个在线可编辑表格的Web应用，要求：
1. 表格可以指定渲染的样式，可以指定特定行列的颜色；
2. 用户在前端可以交互式编辑表格，编辑后后端能够实时收到改动的信息；
3. 在特定单元格可编辑，特定单元格不可编辑；
4. 在每行最后一列添加两个按钮，分别是“删除”和“重运行”，用户点击“删除”按钮时，这一行将被删除，点击“重运行按钮时”，后端接收到指令；
5. 后端会有反馈，修改前端特定单元格的信息；
6. 用户编辑之后自动保存，下次用户访问，或者多个用户访问都得到相同的表格。


注意，启动程序之前，需要：
`docker login registry.sensetime.com/xlab -u sunye2`


内网访问地址：http://10.142.49.243:9110
公网访问地址：http://actvis.cn:9110/

实现效果：

![image](https://user-images.githubusercontent.com/42105752/229693572-1bb498a1-eb9f-4e3b-8adf-faa566698d57.png)
