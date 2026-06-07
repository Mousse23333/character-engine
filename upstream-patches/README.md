# upstream-patches —— 对抗上游覆盖的本地修复记录

这里存放对**上游游戏追踪文件**(`Data/`、`Game/src/` 等)做的小修改。
每次 `git merge upstream` 后这些改动可能被覆盖,本目录让你能快速重新应用。

## 工作流

每个修复一对文件:
- `xxx.md` —— 症状、根因、改法、验证(给人看)
- `xxx.patch` —— `git diff` 生成的补丁(给 `git apply` 用)

合并上游后,逐个重新应用:
```bash
cd "/home/mousse/Documents/Project in progress/Dungeon"
git apply CharacterEngine/upstream-patches/xxx.patch
conda run -n comfyui npx tsc        # 重新编译 out/main.js
```
若 `git apply` 失败(上游改了同一块),打开对应 `.md` 按 diff 手动改。

## 当前补丁清单

| 补丁 | 修什么 | 改动文件 |
|------|--------|----------|
| [blush-fear-group-fix](blush-fear-group-fix.md) | 腮红进游戏不显示 / 恐惧与腮红二选一 | `Data/ModelListFace.ts`(1 行) |
