分析：src/main.py 中的 calculate 函数存在除零错误。

修复方案：将除数从 0 改为 1，同时添加除零保护。

```diff
--- a/src/main.py
+++ b/src/main.py
@@ -4,3 +4,6 @@
 def calculate():
-    return x / 0
+    if x == 0:
+        return 0
+    return x
```

建议同时添加单元测试覆盖边界情况。
