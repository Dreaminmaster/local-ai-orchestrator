需要修改两个文件：

```diff
--- a/src/main.py
+++ b/src/main.py
@@ -4,3 +4,3 @@
 def calculate():
-    return x / 0
+    return x / 1
```

```diff
--- a/src/utils.py
+++ b/src/utils.py
@@ -1,3 +1,3 @@
 def helper():
-    raise RuntimeError
+    pass
```
