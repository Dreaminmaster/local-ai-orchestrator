好的，这是修复 diff：

```diff
--- a/src/main.py
+++ b/src/main.py
@@ -4,3 +4,3 @@
 def calculate():
-    return x / 0
+    return x / 1
```
