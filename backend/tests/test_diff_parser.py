"""
Tests for diff parser
"""
from app.utils.diff_parser import DiffParser


class TestDiffParser:
    """Test cases for DiffParser"""
    
    def test_parse_unified_diff_single_file(self):
        """Test parsing a simple diff with one file"""
        diff = """diff --git a/file.ts b/file.ts
index abc123..def456 100644
--- a/file.ts
+++ b/file.ts
@@ -1,3 +1,4 @@
 const x = 1;
-const y = 2;
+const y = 3;
+const z = 4;
 console.log(x, y);
"""
        files = DiffParser.parse_unified_diff(diff)
        
        assert len(files) == 1
        assert files[0]["filename"] == "file.ts"
        assert files[0]["additions"] == 2
        assert files[0]["deletions"] == 1
        assert len(files[0]["hunks"]) == 1
    
    def test_parse_unified_diff_multiple_files(self):
        """Test parsing diff with multiple files"""
        diff = """diff --git a/file1.ts b/file1.ts
index abc123..def456 100644
--- a/file1.ts
+++ b/file1.ts
@@ -1,2 +1,3 @@
 line 1
+line 2
 line 3
diff --git a/file2.ts b/file2.ts
index 111222..333444 100644
--- a/file2.ts
+++ b/file2.ts
@@ -1,2 +1,2 @@
-old line
+new line
 line 2
"""
        files = DiffParser.parse_unified_diff(diff)
        
        assert len(files) == 2
        assert files[0]["filename"] == "file1.ts"
        assert files[1]["filename"] == "file2.ts"
    
    def test_get_changed_lines(self):
        """Test extracting changed lines with line numbers"""
        diff = """diff --git a/file.ts b/file.ts
index abc123..def456 100644
--- a/file.ts
+++ b/file.ts
@@ -1,2 +1,3 @@
 line 1
+line 2
 line 3
"""
        changed = DiffParser.get_changed_lines(diff)
        
        assert "file.ts" in changed
        assert len(changed["file.ts"]) == 1
        assert changed["file.ts"][0] == (2, "line 2")
    
    def test_get_file_stats(self):
        """Test getting file statistics"""
        diff = """diff --git a/file.ts b/file.ts
index abc123..def456 100644
--- a/file.ts
+++ b/file.ts
@@ -1,3 +1,4 @@
 line 1
-line 2
+line 2 modified
+line 3
 line 4
"""
        stats = DiffParser.get_file_stats(diff)
        
        assert "file.ts" in stats
        assert stats["file.ts"]["additions"] == 2
        assert stats["file.ts"]["deletions"] == 1
        assert stats["file.ts"]["changes"] == 3
