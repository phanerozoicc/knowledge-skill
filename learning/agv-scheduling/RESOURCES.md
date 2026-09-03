# AGV / 机器人调度系统 学习资源

> 原则:**高信任优先**。优先教材、综述论文、行业协议规范、公认专家的工程文章。营销内容一律不入。
> 每条标注:**是什么 / 用于哪个单元 / 何时翻它**。
> 随课程推进持续补充。当前为初始版,将在 L0-01 课中确认并增补。

## Knowledge(知识与教材)

### 综述与教材(高信任地基)
- [Book: _Wheeled Mobile Robotics* — Sigaud 等](https://www.sciencedirect.com/book/9780128042045/wheeled-mobile-robotics)
  移动机器人全方位教材,涵盖运动学、控制、导航、SLAM。**用于**:L1 运动/控制、HW 底盘。何时翻:需要把某个运动学概念弄严谨时。
- [Book: _Computational Intelligence in Multi-Agent Systems_ — Springer](https://link.springer.com/book/10.1007/978-3-030-63264-9)
  多智能体系统方法论。**用于**:L2 任务分配、L4 MRS。
- [Survey: "Multi-Agent Path Finding (MAPF)" — Stern et al.](https://arxiv.org/abs/2105.01626) *(待核实最新版本)*
  MAPF 问题定义与算法综述。**用于**:L2-03、L2-04。何时翻:把 MAPF 形式化、比较算法时。

### 算法(经典,高信任)
- [Red Blob Games: A* Pathfinding — Amit Patel](https://www.redblobgames.com/pathfinding/a-star/introduction.html)
  公认最好的 A* 可视化讲解,交互式。**用于**:L1-03 Dijkstra、L1-04 A*。**必看**。
- [Wikipedia: Conflict-Based Search (CBS)](https://en.wikipedia.org/wiki/Multi-agent_path_finding#Conflict-Based_Search)
  CBS 算法概念入门。**用于**:L2-04。深入需配论文。

### 工业协议与工程(权威规范)
- [VDA 5050 v2.0 规范 (PDF)](https://www.vda.de/en/services/Publications/vda-5050-version-2.0-.html)
  德国汽车工业协会 AGV 通信标准,事实上的行业接入规范。**用于**:L3-03。**必读**。
- [OPC UA Robotics Companion Spec](https://opcfoundation.org/about/opc-technologies/robotics/)
  工业机器人通信规范,了解工业侧的另一种思路。**用于**:L3-03 拓展。

### 行业/架构(实践派,需交叉验证)
- *(待补充:待核实后再列入,避免营销内容)*

## Wisdom(社区与实战)

- [r/robotics](https://reddit.com/r/robotics) — 通用机器人社区,入门问答
- [ROS Discourse](https://discourse.ros.org/) — ROS 官方论坛,工程实践讨论密集。**用于**:L3/L5、HW
- [Stack Exchange: Robotics](https://robotics.stackexchange.com/) — 概念与算法问答
- *(中国社区待评估后补充)*

## Gaps(目前缺口)

- **中文高质量资源**:目前较少列入,将在学习中按需评估补充
- **真实仓库/工厂调度案例的深度技术文章**:大多在厂商白皮书里,营销成分重,需筛选
- **人形/具身调度**:领域新,系统教材少,主要靠综述论文 + 厂商技术博客(待筛选)

## 使用约定
- 任何新资源加入前,问三个问题:① 是否高信任(教材/规范/公认专家)? ② 对应哪个单元? ③ 何时会回来翻它?三个都有答案才加入。
- 资源过时或发现错误,直接移除,不要堆积。
