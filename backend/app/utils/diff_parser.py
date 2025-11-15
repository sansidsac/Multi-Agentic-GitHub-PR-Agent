"""
Diff parser utility for processing unified diffs
"""
import re
from typing import List, Dict, Any, Tuple


class DiffParser:
    """Parser for unified diff format"""
    
    @staticmethod
    def parse_unified_diff(diff_text: str) -> List[Dict[str, Any]]:
        """
        Parse unified diff into structured format
        
        Args:
            diff_text: Unified diff string
            
        Returns:
            List of file changes with hunks
        """
        files = []
        current_file = None
        current_hunk = None
        
        for line in diff_text.split("\n"):
            # File header (diff --git a/file b/file)
            if line.startswith("diff --git"):
                if current_file:
                    files.append(current_file)
                
                match = re.search(r"b/(.+)$", line)
                filename = match.group(1) if match else "unknown"
                
                current_file = {
                    "filename": filename,
                    "hunks": [],
                    "additions": 0,
                    "deletions": 0
                }
                current_hunk = None
            
            # Hunk header (@@ -start,count +start,count @@)
            elif line.startswith("@@"):
                if current_file:
                    match = re.search(r"@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@", line)
                    if match:
                        old_start = int(match.group(1))
                        new_start = int(match.group(3))
                        
                        current_hunk = {
                            "old_start": old_start,
                            "new_start": new_start,
                            "changes": []
                        }
                        current_file["hunks"].append(current_hunk)
            
            # Content lines
            elif current_hunk is not None:
                if line.startswith("+") and not line.startswith("+++"):
                    current_hunk["changes"].append({"type": "add", "content": line[1:]})
                    current_file["additions"] += 1
                elif line.startswith("-") and not line.startswith("---"):
                    current_hunk["changes"].append({"type": "del", "content": line[1:]})
                    current_file["deletions"] += 1
                elif line.startswith(" "):
                    current_hunk["changes"].append({"type": "context", "content": line[1:]})
        
        # Add last file
        if current_file:
            files.append(current_file)
        
        return files
    
    @staticmethod
    def get_changed_lines(diff_text: str) -> Dict[str, List[Tuple[int, str]]]:
        """
        Extract changed lines with line numbers
        
        Args:
            diff_text: Unified diff string
            
        Returns:
            Dictionary mapping filename to list of (line_number, content) tuples
        """
        files = DiffParser.parse_unified_diff(diff_text)
        changed_lines = {}
        
        for file in files:
            filename = file["filename"]
            lines = []
            
            for hunk in file["hunks"]:
                line_num = hunk["new_start"]
                
                for change in hunk["changes"]:
                    if change["type"] == "add":
                        lines.append((line_num, change["content"]))
                        line_num += 1
                    elif change["type"] == "context":
                        line_num += 1
            
            if lines:
                changed_lines[filename] = lines
        
        return changed_lines
    
    @staticmethod
    def get_file_stats(diff_text: str) -> Dict[str, Dict[str, int]]:
        """
        Get statistics for each file in diff
        
        Args:
            diff_text: Unified diff string
            
        Returns:
            Dictionary mapping filename to stats (additions, deletions)
        """
        files = DiffParser.parse_unified_diff(diff_text)
        stats = {}
        
        for file in files:
            stats[file["filename"]] = {
                "additions": file["additions"],
                "deletions": file["deletions"],
                "changes": file["additions"] + file["deletions"]
            }
        
        return stats
