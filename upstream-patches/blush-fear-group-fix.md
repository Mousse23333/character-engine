# 修复:腮红(Blush)在游戏里不显示 / 恐惧与腮红二选一

> 这是一个**改了上游追踪文件**的补丁。每次 `git merge upstream` 后,如果上游重写了这块,修改会被覆盖,需要按本文重新应用。

## 症状(出现任意一条即是本问题)

- 在衣橱里能选腮红,但**进游戏腮红不显示**;手动加好几遍,一进游戏就没了。
- 衣橱里**恐惧表情(Fear)和腮红(Blush)只能二选一**,选一个另一个自动取消。
- 表情/兴奋度变化、手动强制 pose 都无法让腮红出现。

## 根本原因

`Fear` 模型的基础 `Group` 被定义成了 `"Blush"`,和腮红模型(KjusBlush / KoiBlush)**抢同一个装备槽**。

- 衣橱按"同组互斥"处理 → 恐惧和腮红只能留一个。
- `KinkyDungeonDress.ts` 里有一段:角色没有 `Fear` pose 时,自动把 `Fear` 以默认组 `"Blush"` 穿上(`KDInventoryWear(Character, "Fear", undefined, ...)`)。于是每次换装刷新都把 Fear 塞回 Blush 槽,顶掉手动加的腮红。

游戏自带的脸部样式(如 `Default`)其实是靠 `{"Item":"Fear","Group":"Fear"}` 把 Fear 改到独立组来规避这个坑的。本补丁就是把**基础定义**对齐到这个正确行为。

> 注意:这**不是** OS / Linux / WebP / 纹理图集 / 渲染的问题——那些都验证排除过。贴图、图集、渲染一切正常,纯粹是"模型因为同组冲突被清掉、根本没装到角色身上"。验证方法见文末。

## 修复(一行)

文件:`Data/ModelListFace.ts`,`Fear` 模型定义处(`Name: "Fear"` 那个 `AddModel`):

```diff
 	Name: "Fear",
 	Folder: "Expressions",
 	TopLevel: true,
 	Protected: true,
-	Group: "Blush",
+	Group: "Fear",
 	Categories: ["Face"],
 	AddPose: ["Fear"],
```

`"Fear"` 组在 `Data/Defs.ts` 里已存在(`Fear: { Parent: "Head" }`),无需额外注册。

### 一键应用

```bash
cd "/home/mousse/Documents/Project in progress/Dungeon"
git apply CharacterEngine/upstream-patches/blush-fear-group-fix.patch
conda run -n comfyui npx tsc          # 重新编译 out/main.js(约 20 秒)
```

若 `git apply` 因上游改动而失败,就按上面的 diff 手动改那一行(搜 `Name: "Fear"` → 把它下面的 `Group: "Blush"` 改成 `Group: "Fear"`)。

## 生效后的处理(重要)

旧存档里已经穿着的 Fear **仍带着老的 "Blush" 组**(组信息在装备时被复制进了存档)。硬刷新游戏(`Ctrl+Shift+R`)后,在浏览器控制台跑一次,让游戏用新组重穿:

```js
KinkyDungeonPlayer.Appearance = KinkyDungeonPlayer.Appearance.filter(a => a.Model?.Name !== "Fear");
KinkyDungeonDressPlayer();
```

之后衣橱里恐惧和腮红就是两个独立槽,可同时拥有,腮红进游戏也留得住。

## 可选:双保险(让所有角色/存档默认生效)

如果不想每次清 Fear,可再把自动穿 Fear 那行也显式指定组。文件 `Game/src/player/KinkyDungeonDress.ts`(约 863 行):

```diff
-		KDInventoryWear(Character, "Fear",
-			undefined, undefined, undefined,
+		KDInventoryWear(Character, "Fear",
+			"Fear", undefined, undefined,
 			undefined, undefined);
```

本次只应用了上面的"一行"主修复,这条双保险**未应用**,需要时再加。

## 验证(确认修好了)

浏览器控制台:

```js
// 模型集合里应同时能见到 Fear 和某个 Blush 模型(KjusBlush/KoiBlush),不再互斥
[...KDCurrentModels.get(KinkyDungeonPlayer).Models.keys()].filter(k => /blush|fear/i.test(k))
```

—— 当年定位用的命令(留作参考):
- `[...KDCurrentModels.get(KinkyDungeonPlayer).Models.keys()]` —— 看 Blush 槽装的是不是 Fear
- `Object.keys(PIXI.utils.TextureCache).filter(k => /blush/i.test(k))` —— 证明贴图本就已加载(排除图集/webp 问题)

---
定位 + 修复日期:2026-06-07。改动文件:`Data/ModelListFace.ts`(1 行)。
