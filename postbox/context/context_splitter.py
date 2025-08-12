#!/usr/bin/env python3
"""
Context Splitter for Gemini Capability Enhancement
Flash 2.5の2000トークン制限対応コンテキスト分割システム
"""

import json
import os
import re
import ast
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

class SplitStrategy(Enum):
    """分割戦略タイプ"""
    FUNCTION_BASED = "function_based"      # 関数単位分割
    CLASS_BASED = "class_based"            # クラス単位分割
    MODULE_BASED = "module_based"          # モジュール単位分割
    DEPENDENCY_BASED = "dependency_based"  # 依存関係基準分割
    TOKEN_BASED = "token_based"            # トークン数基準分割

@dataclass
class ContextChunk:
    """コンテキストチャンク（分割単位）"""
    chunk_id: str
    content: str
    estimated_tokens: int
    dependencies: List[str]
    priority: int
    chunk_type: str
    metadata: Dict[str, Any]
    execution_order: int = 0
    parent_task_id: str = ""
    
class DependencyAnalyzer:
    """依存関係解析器"""
    
    def __init__(self):
        self.import_patterns = [
            r'from\s+(\w+(?:\.\w+)*)\s+import',
            r'import\s+(\w+(?:\.\w+)*)',
        ]
        self.call_patterns = [
            r'(\w+)\s*\(',  # 関数呼び出し
            r'(\w+)\.(\w+)',  # メソッド呼び出し
            r'class\s+(\w+)\s*\(',  # クラス継承
        ]
    
    def analyze_code_dependencies(self, code: str, context: Dict[str, Any]) -> List[str]:
        """コード依存関係分析"""
        dependencies = set()
        
        try:
            # AST解析による依存関係抽出
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.add(node.module)
                elif isinstance(node, ast.FunctionDef):
                    # 関数内で使用されている外部参照を分析
                    for child in ast.walk(node):
                        if isinstance(child, ast.Name):
                            dependencies.add(child.id)
                        elif isinstance(child, ast.Attribute):
                            if isinstance(child.value, ast.Name):
                                dependencies.add(child.value.id)
        
        except SyntaxError:
            # 構文エラーの場合は正規表現で基本的な依存関係を抽出
            for pattern in self.import_patterns:
                matches = re.findall(pattern, code)
                dependencies.update(matches)
        
        # フィルタリング：Python標準ライブラリや明らかに不要なものを除外
        filtered_deps = []
        builtin_modules = {'typing', 'os', 'sys', 'json', 're', 'datetime', 'pathlib'}
        
        for dep in dependencies:
            if dep not in builtin_modules and len(dep) > 1 and not dep.startswith('_'):
                filtered_deps.append(dep)
        
        return filtered_deps
    
    def analyze_task_dependencies(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """タスク間依存関係分析"""
        dependency_graph = {}
        
        for task in tasks:
            task_id = task.get('task_id', '')
            task_type = task.get('type', '')
            target_files = task.get('target_files', [])
            
            deps = set()
            
            # ファイル間依存関係
            for file_path in target_files:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        file_deps = self.analyze_code_dependencies(content, task)
                        deps.update(file_deps)
                    
                    except Exception:
                        continue
            
            # タスクタイプ基準の依存関係
            if task_type in ['hybrid_implementation', 'new_feature_development']:
                deps.add('base_implementation')
            
            dependency_graph[task_id] = list(deps)
        
        return dependency_graph
    
    def calculate_execution_order(self, dependency_graph: Dict[str, List[str]]) -> List[str]:
        """実行順序計算（トポロジカルソート）"""
        
        # 簡易版トポロジカルソート
        in_degree = {}
        nodes = set(dependency_graph.keys())
        
        # 初期化
        for node in nodes:
            in_degree[node] = 0
        
        # 入次数計算
        for node, deps in dependency_graph.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1
        
        # 実行順序決定
        execution_order = []
        queue = [node for node, degree in in_degree.items() if degree == 0]
        
        while queue:
            current = queue.pop(0)
            execution_order.append(current)
            
            # 依存関係を更新
            if current in dependency_graph:
                for dep in dependency_graph[current]:
                    if dep in in_degree:
                        in_degree[dep] -= 1
                        if in_degree[dep] == 0:
                            queue.append(dep)
        
        return execution_order

class ContextSplitter:
    """
    コンテキスト分割エンジン
    Flash 2.5の2000トークン制限に対応した自動分割システム
    """
    
    def __init__(self, max_tokens_per_chunk: int = 1800):
        """
        初期化
        
        Args:
            max_tokens_per_chunk: チャンク当たりの最大トークン数（余裕を持って1800）
        """
        self.max_tokens_per_chunk = max_tokens_per_chunk
        self.dependency_analyzer = DependencyAnalyzer()
        self.token_estimator = TokenEstimator()
        
        # 分割戦略の優先順位
        self.strategy_priority = [
            SplitStrategy.FUNCTION_BASED,
            SplitStrategy.CLASS_BASED,
            SplitStrategy.MODULE_BASED,
            SplitStrategy.DEPENDENCY_BASED,
            SplitStrategy.TOKEN_BASED
        ]
    
    def split_implementation_task(self, task_data: Dict[str, Any]) -> List[ContextChunk]:
        """
        新規実装タスクの分割
        
        Args:
            task_data: 実装タスクデータ
            
        Returns:
            分割されたコンテキストチャンクリスト
        """
        
        task_type = task_data.get('type', '')
        implementation_spec = task_data.get('requirements', {}).get('implementation_spec', {})
        target_files = task_data.get('target_files', [])
        
        print(f"🔄 実装タスク分割開始: {task_type}")
        print(f"📁 対象ファイル: {len(target_files)}件")
        
        chunks = []
        
        # 実装タイプ別分割戦略
        if task_type == "new_implementation":
            chunks = self._split_new_implementation(task_data, implementation_spec)
        elif task_type == "hybrid_implementation":
            chunks = self._split_hybrid_implementation(task_data, implementation_spec)
        elif task_type == "new_feature_development":
            chunks = self._split_feature_development(task_data, implementation_spec)
        else:
            # 汎用分割
            chunks = self._split_generic_task(task_data)
        
        # 依存関係解析・実行順序決定
        chunks = self._analyze_and_order_chunks(chunks, task_data)
        
        print(f"✅ 分割完了: {len(chunks)}チャンク生成")
        return chunks
    
    def split_modification_task(self, task_data: Dict[str, Any]) -> List[ContextChunk]:
        """
        コード修正タスクの分割
        
        Args:
            task_data: 修正タスクデータ
            
        Returns:
            分割されたコンテキストチャンクリスト  
        """
        
        target_files = task_data.get('target_files', [])
        error_type = task_data.get('requirements', {}).get('error_type', '')
        
        print(f"🔄 修正タスク分割開始: {error_type}")
        print(f"📁 対象ファイル: {len(target_files)}件")
        
        chunks = []
        
        # ファイル単位で分割
        for i, file_path in enumerate(target_files):
            if not os.path.exists(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                # ファイルサイズによる分割戦略決定
                estimated_tokens = self.token_estimator.estimate_tokens(file_content)
                
                if estimated_tokens <= self.max_tokens_per_chunk:
                    # 単一チャンクで処理可能
                    chunk = self._create_file_chunk(file_path, file_content, task_data, i)
                    chunks.append(chunk)
                else:
                    # 関数・クラス単位で分割
                    file_chunks = self._split_large_file(file_path, file_content, task_data, i)
                    chunks.extend(file_chunks)
            
            except Exception as e:
                print(f"⚠️ ファイル分割エラー {file_path}: {e}")
                continue
        
        # 依存関係解析・実行順序決定
        chunks = self._analyze_and_order_chunks(chunks, task_data)
        
        print(f"✅ 分割完了: {len(chunks)}チャンク生成")
        return chunks
    
    def _split_new_implementation(self, task_data: Dict[str, Any], 
                                implementation_spec: Dict[str, Any]) -> List[ContextChunk]:
        """新規実装の分割"""
        
        chunks = []
        target_files = task_data.get('target_files', [])
        template_type = implementation_spec.get('template_type', 'class')
        
        for i, file_path in enumerate(target_files):
            # ファイル単位でチャンク作成
            chunk_content = self._generate_implementation_context(
                file_path, template_type, implementation_spec
            )
            
            chunk = ContextChunk(
                chunk_id=f"impl_{i:03d}_{Path(file_path).stem}",
                content=chunk_content,
                estimated_tokens=self.token_estimator.estimate_tokens(chunk_content),
                dependencies=self._extract_implementation_dependencies(implementation_spec),
                priority=self._calculate_priority(file_path, template_type),
                chunk_type="new_implementation",
                metadata={
                    "file_path": file_path,
                    "template_type": template_type,
                    "implementation_spec": implementation_spec
                },
                parent_task_id=task_data.get('task_id', '')
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _split_hybrid_implementation(self, task_data: Dict[str, Any],
                                   implementation_spec: Dict[str, Any]) -> List[ContextChunk]:
        """ハイブリッド実装の分割"""
        
        chunks = []
        target_files = task_data.get('target_files', [])
        
        for i, file_path in enumerate(target_files):
            if os.path.exists(file_path):
                # 既存ファイル修正
                chunk = self._create_modification_chunk(file_path, task_data, i, "hybrid_modify")
            else:
                # 新規ファイル作成
                chunk = self._create_creation_chunk(file_path, implementation_spec, i, "hybrid_create")
            
            chunks.append(chunk)
        
        return chunks
    
    def _split_feature_development(self, task_data: Dict[str, Any],
                                 feature_spec: Dict[str, Any]) -> List[ContextChunk]:
        """新機能開発の分割"""
        
        chunks = []
        implementation_plan = feature_spec.get('implementation_plan', [])
        
        for i, step in enumerate(implementation_plan):
            step_type = step.get('type', 'implementation')
            step_files = step.get('files', [])
            
            chunk_content = self._generate_feature_context(step, feature_spec)
            
            chunk = ContextChunk(
                chunk_id=f"feat_{i:03d}_{step_type}",
                content=chunk_content,
                estimated_tokens=self.token_estimator.estimate_tokens(chunk_content),
                dependencies=self._extract_feature_dependencies(step, feature_spec),
                priority=step.get('priority', 5),
                chunk_type="feature_development",
                metadata={
                    "step_type": step_type,
                    "step_files": step_files,
                    "feature_spec": feature_spec
                },
                parent_task_id=task_data.get('task_id', '')
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _split_generic_task(self, task_data: Dict[str, Any]) -> List[ContextChunk]:
        """汎用タスクの分割"""
        
        chunks = []
        target_files = task_data.get('target_files', [])
        
        if not target_files:
            # ファイルがない場合は単一チャンクとして作成
            chunk = ContextChunk(
                chunk_id="generic_001",
                content=json.dumps(task_data, indent=2, ensure_ascii=False),
                estimated_tokens=500,
                dependencies=[],
                priority=5,
                chunk_type="generic",
                metadata=task_data,
                parent_task_id=task_data.get('task_id', '')
            )
            chunks.append(chunk)
        else:
            # ファイル単位で分割
            for i, file_path in enumerate(target_files):
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    chunk = self._create_file_chunk(file_path, content, task_data, i)
                    chunks.append(chunk)
        
        return chunks
    
    def _split_large_file(self, file_path: str, content: str, 
                         task_data: Dict[str, Any], base_index: int) -> List[ContextChunk]:
        """大きなファイルの分割"""
        
        chunks = []
        
        try:
            # AST解析で関数・クラス単位に分割
            tree = ast.parse(content)
            
            functions = []
            classes = []
            imports = []
            other_code = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_start = node.lineno - 1
                    func_end = getattr(node, 'end_lineno', func_start + 10) - 1
                    func_content = '\n'.join(content.split('\n')[func_start:func_end + 1])
                    functions.append((node.name, func_content, func_start, func_end))
                
                elif isinstance(node, ast.ClassDef):
                    class_start = node.lineno - 1
                    class_end = getattr(node, 'end_lineno', class_start + 20) - 1
                    class_content = '\n'.join(content.split('\n')[class_start:class_end + 1])
                    classes.append((node.name, class_content, class_start, class_end))
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_line = node.lineno - 1
                    import_content = content.split('\n')[import_line]
                    imports.append(import_content)
            
            # import文の統合
            import_chunk = '\n'.join(imports) if imports else ""
            
            # 関数単位のチャンク作成
            for i, (func_name, func_content, start, end) in enumerate(functions):
                chunk_content = import_chunk + '\n\n' + func_content
                
                if self.token_estimator.estimate_tokens(chunk_content) <= self.max_tokens_per_chunk:
                    chunk = ContextChunk(
                        chunk_id=f"func_{base_index:03d}_{i:03d}_{func_name}",
                        content=chunk_content,
                        estimated_tokens=self.token_estimator.estimate_tokens(chunk_content),
                        dependencies=self.dependency_analyzer.analyze_code_dependencies(
                            func_content, task_data
                        ),
                        priority=self._calculate_function_priority(func_name),
                        chunk_type="function_modification",
                        metadata={
                            "file_path": file_path,
                            "function_name": func_name,
                            "line_range": (start, end)
                        },
                        parent_task_id=task_data.get('task_id', '')
                    )
                    chunks.append(chunk)
            
            # クラス単位のチャンク作成
            for i, (class_name, class_content, start, end) in enumerate(classes):
                chunk_content = import_chunk + '\n\n' + class_content
                
                if self.token_estimator.estimate_tokens(chunk_content) <= self.max_tokens_per_chunk:
                    chunk = ContextChunk(
                        chunk_id=f"class_{base_index:03d}_{i:03d}_{class_name}",
                        content=chunk_content,
                        estimated_tokens=self.token_estimator.estimate_tokens(chunk_content),
                        dependencies=self.dependency_analyzer.analyze_code_dependencies(
                            class_content, task_data
                        ),
                        priority=self._calculate_class_priority(class_name),
                        chunk_type="class_modification",
                        metadata={
                            "file_path": file_path,
                            "class_name": class_name,
                            "line_range": (start, end)
                        },
                        parent_task_id=task_data.get('task_id', '')
                    )
                    chunks.append(chunk)
        
        except SyntaxError:
            # 構文エラーの場合は行数ベースで分割
            lines = content.split('\n')
            chunk_size = self.max_tokens_per_chunk // 4  # 1行約4トークンと仮定
            
            for i in range(0, len(lines), chunk_size):
                chunk_lines = lines[i:i + chunk_size]
                chunk_content = '\n'.join(chunk_lines)
                
                chunk = ContextChunk(
                    chunk_id=f"lines_{base_index:03d}_{i:03d}",
                    content=chunk_content,
                    estimated_tokens=self.token_estimator.estimate_tokens(chunk_content),
                    dependencies=[],
                    priority=5,
                    chunk_type="line_based_modification",
                    metadata={
                        "file_path": file_path,
                        "line_range": (i, i + len(chunk_lines))
                    },
                    parent_task_id=task_data.get('task_id', '')
                )
                chunks.append(chunk)
        
        return chunks
    
    def _create_file_chunk(self, file_path: str, content: str, 
                          task_data: Dict[str, Any], index: int) -> ContextChunk:
        """ファイル単位のチャンク作成"""
        
        return ContextChunk(
            chunk_id=f"file_{index:03d}_{Path(file_path).stem}",
            content=content,
            estimated_tokens=self.token_estimator.estimate_tokens(content),
            dependencies=self.dependency_analyzer.analyze_code_dependencies(content, task_data),
            priority=self._calculate_file_priority(file_path),
            chunk_type="file_modification",
            metadata={
                "file_path": file_path,
                "task_type": task_data.get('type', 'modification')
            },
            parent_task_id=task_data.get('task_id', '')
        )
    
    def _create_modification_chunk(self, file_path: str, task_data: Dict[str, Any],
                                 index: int, chunk_type: str) -> ContextChunk:
        """修正チャンク作成"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return ContextChunk(
            chunk_id=f"modify_{index:03d}_{Path(file_path).stem}",
            content=content,
            estimated_tokens=self.token_estimator.estimate_tokens(content),
            dependencies=self.dependency_analyzer.analyze_code_dependencies(content, task_data),
            priority=self._calculate_file_priority(file_path),
            chunk_type=chunk_type,
            metadata={
                "file_path": file_path,
                "exists": True,
                "modification_type": "extend"
            },
            parent_task_id=task_data.get('task_id', '')
        )
    
    def _create_creation_chunk(self, file_path: str, implementation_spec: Dict[str, Any],
                             index: int, chunk_type: str) -> ContextChunk:
        """作成チャンク作成"""
        
        template_content = self._generate_implementation_context(
            file_path, implementation_spec.get('template_type', 'class'), implementation_spec
        )
        
        return ContextChunk(
            chunk_id=f"create_{index:03d}_{Path(file_path).stem}",
            content=template_content,
            estimated_tokens=self.token_estimator.estimate_tokens(template_content),
            dependencies=self._extract_implementation_dependencies(implementation_spec),
            priority=self._calculate_file_priority(file_path),
            chunk_type=chunk_type,
            metadata={
                "file_path": file_path,
                "exists": False,
                "template_type": implementation_spec.get('template_type', 'class')
            },
            parent_task_id=implementation_spec.get('task_id', '')
        )
    
    def _generate_implementation_context(self, file_path: str, template_type: str,
                                       implementation_spec: Dict[str, Any]) -> str:
        """実装コンテキスト生成"""
        
        context = f"""
# 新規実装コンテキスト - {Path(file_path).name}

## 実装仕様
- ファイルパス: {file_path}
- テンプレートタイプ: {template_type}

## 実装詳細
{json.dumps(implementation_spec, indent=2, ensure_ascii=False)}

## Flash 2.5実行指示
1. 上記仕様に基づいて{template_type}タイプの実装を作成
2. 全ての関数・メソッドに適切な型注釈を追加
3. 適切なdocstringを追加
4. mypy strict mode に適合する実装を作成
5. 実装完了後、構文チェックを実行

## 品質要件
- 型注釈必須 (typing.Any使用可)
- docstring必須
- PEP8準拠
- mypy strict mode適合
"""
        
        return context
    
    def _generate_feature_context(self, step: Dict[str, Any], 
                                feature_spec: Dict[str, Any]) -> str:
        """機能実装コンテキスト生成"""
        
        context = f"""
# 機能開発コンテキスト - {feature_spec.get('name', 'new_feature')}

## 開発ステップ
{json.dumps(step, indent=2, ensure_ascii=False)}

## 機能仕様
{json.dumps(feature_spec, indent=2, ensure_ascii=False)}

## Flash 2.5実行指示
1. 上記ステップに基づいて機能実装を実行
2. 既存コードとの整合性を確保
3. 適切なテスト作成（必要に応じて）
4. ドキュメント更新
5. 品質チェック実行

## 品質要件
- 既存機能への影響最小化
- 適切なエラーハンドリング
- 十分なテスト網羅率
- 保守性の高いコード設計
"""
        
        return context
    
    def _extract_implementation_dependencies(self, implementation_spec: Dict[str, Any]) -> List[str]:
        """実装仕様から依存関係抽出"""
        
        deps = []
        
        # 基本的な依存関係
        imports = implementation_spec.get('imports', [])
        for imp in imports:
            if 'import' in imp:
                # import文から依存関係を抽出
                if 'from' in imp:
                    module = imp.split('from')[1].split('import')[0].strip()
                    deps.append(module)
                else:
                    module = imp.replace('import', '').strip()
                    deps.append(module)
        
        # 基底クラスから依存関係を抽出
        base_classes = implementation_spec.get('base_classes', [])
        deps.extend(base_classes)
        
        return deps
    
    def _extract_feature_dependencies(self, step: Dict[str, Any], 
                                    feature_spec: Dict[str, Any]) -> List[str]:
        """機能ステップから依存関係抽出"""
        
        deps = []
        
        # ステップタイプに基づく依存関係
        step_type = step.get('type', '')
        if step_type == 'modify':
            deps.append('existing_implementation')
        elif step_type == 'create':
            deps.extend(step.get('dependencies', []))
        
        # 機能仕様から依存関係
        feature_deps = feature_spec.get('dependencies', [])
        deps.extend(feature_deps)
        
        return deps
    
    def _analyze_and_order_chunks(self, chunks: List[ContextChunk], 
                                task_data: Dict[str, Any]) -> List[ContextChunk]:
        """チャンク依存関係解析・実行順序決定"""
        
        # 依存関係グラフ構築
        dependency_graph = {}
        for chunk in chunks:
            dependency_graph[chunk.chunk_id] = chunk.dependencies
        
        # 実行順序計算
        execution_order = self.dependency_analyzer.calculate_execution_order(dependency_graph)
        
        # 実行順序をチャンクに設定
        for i, chunk_id in enumerate(execution_order):
            for chunk in chunks:
                if chunk.chunk_id == chunk_id:
                    chunk.execution_order = i
                    break
        
        # 実行順序でソート
        chunks.sort(key=lambda x: (x.execution_order, x.priority, x.chunk_id))
        
        return chunks
    
    def _calculate_priority(self, file_path: str, template_type: str) -> int:
        """優先度計算"""
        
        priority = 5  # デフォルト
        
        # ファイル名による優先度
        filename = Path(file_path).name.lower()
        if 'main' in filename or '__init__' in filename:
            priority = 1  # 最高優先度
        elif 'config' in filename or 'setting' in filename:
            priority = 2
        elif 'util' in filename or 'helper' in filename:
            priority = 3
        elif 'test' in filename:
            priority = 8  # 低優先度
        
        # テンプレートタイプによる優先度調整
        if template_type == 'class':
            priority -= 1
        elif template_type == 'module':
            priority -= 0
        elif template_type == 'function':
            priority += 1
        
        return max(1, min(priority, 10))
    
    def _calculate_file_priority(self, file_path: str) -> int:
        """ファイル優先度計算"""
        return self._calculate_priority(file_path, 'file')
    
    def _calculate_function_priority(self, func_name: str) -> int:
        """関数優先度計算"""
        
        if func_name.startswith('__'):
            return 2  # 特殊メソッドは高優先度
        elif func_name.startswith('_'):
            return 7  # プライベート関数は低優先度
        elif func_name in ['main', 'init', 'setup']:
            return 1  # 主要関数は最高優先度
        else:
            return 5  # デフォルト
    
    def _calculate_class_priority(self, class_name: str) -> int:
        """クラス優先度計算"""
        
        if 'Manager' in class_name or 'Controller' in class_name:
            return 2  # 管理クラスは高優先度
        elif 'Helper' in class_name or 'Util' in class_name:
            return 6  # ユーティリティは低優先度
        elif 'Test' in class_name:
            return 8  # テストクラスは低優先度
        else:
            return 4  # デフォルト
    
    def save_chunks_to_files(self, chunks: List[ContextChunk], 
                           output_dir: str = "tmp/context_chunks") -> List[str]:
        """分割されたチャンクをファイルに保存"""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        
        for chunk in chunks:
            chunk_filename = f"{chunk.chunk_id}.json"
            chunk_filepath = output_path / chunk_filename
            
            # チャンクデータを辞書に変換
            chunk_data = asdict(chunk)
            
            # ファイルに保存
            with open(chunk_filepath, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, indent=2, ensure_ascii=False)
            
            saved_files.append(str(chunk_filepath))
        
        print(f"💾 {len(chunks)}チャンクを{output_dir}に保存しました")
        return saved_files
    
    def load_chunks_from_files(self, chunk_dir: str) -> List[ContextChunk]:
        """ファイルからチャンクを読み込み"""
        
        chunks = []
        chunk_path = Path(chunk_dir)
        
        if not chunk_path.exists():
            return chunks
        
        for chunk_file in chunk_path.glob("*.json"):
            try:
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
                
                chunk = ContextChunk(**chunk_data)
                chunks.append(chunk)
                
            except Exception as e:
                print(f"⚠️ チャンク読み込みエラー {chunk_file}: {e}")
                continue
        
        # 実行順序でソート
        chunks.sort(key=lambda x: (x.execution_order, x.priority, x.chunk_id))
        
        return chunks


class TokenEstimator:
    """トークン数推定器"""
    
    def __init__(self):
        # 日本語・英語混在テキストの平均的なトークン変換率
        self.avg_chars_per_token = 3.5
        
        # コードの特性を考慮した調整係数
        self.code_adjustment = 1.2  # コードは通常のテキストより若干多くのトークンを使用
    
    def estimate_tokens(self, text: str) -> int:
        """テキストのトークン数を推定"""
        
        if not text:
            return 0
        
        # 基本的な文字数ベースの推定
        base_estimate = len(text) / self.avg_chars_per_token
        
        # コード特性の考慮
        code_factor = self._analyze_code_characteristics(text)
        adjusted_estimate = base_estimate * (1 + code_factor * 0.2)
        
        return int(adjusted_estimate * self.code_adjustment)
    
    def _analyze_code_characteristics(self, text: str) -> float:
        """コード特性分析"""
        
        # コード的特徴のスコアリング
        code_indicators = [
            (r'def\s+\w+\s*\(', 0.1),    # 関数定義
            (r'class\s+\w+\s*\(', 0.1),  # クラス定義
            (r'import\s+\w+', 0.05),     # import文
            (r'from\s+\w+\s+import', 0.05), # from import文
            (r'[{}()\[\]]', 0.02),       # 括弧類
            (r'[=+\-*/]', 0.01),         # 演算子
        ]
        
        score = 0.0
        for pattern, weight in code_indicators:
            matches = len(re.findall(pattern, text))
            score += matches * weight
        
        # 正規化（最大1.0）
        return min(score / len(text.split('\n')), 1.0)


def main():
    """テスト実行"""
    
    splitter = ContextSplitter()
    
    # テストタスク：新規実装
    test_task = {
        'task_id': 'test_implementation_001',
        'type': 'new_implementation',
        'target_files': [
            'postbox/context/test_new_class.py',
            'postbox/context/test_utility.py'
        ],
        'requirements': {
            'implementation_spec': {
                'template_type': 'class',
                'class_name': 'TestContextManager',
                'methods': ['__init__', 'process', 'validate'],
                'imports': ['from typing import Dict, List, Any'],
                'description': 'テスト用コンテキスト管理クラス'
            }
        }
    }
    
    print("🧪 ContextSplitter テスト実行")
    
    # 実装タスク分割テスト
    chunks = splitter.split_implementation_task(test_task)
    
    print(f"\n📊 分割結果:")
    for i, chunk in enumerate(chunks):
        print(f"{i+1}. {chunk.chunk_id}")
        print(f"   トークン数: {chunk.estimated_tokens}")
        print(f"   優先度: {chunk.priority}")
        print(f"   実行順序: {chunk.execution_order}")
        print(f"   依存関係: {chunk.dependencies}")
        print()
    
    # チャンクの保存テスト
    saved_files = splitter.save_chunks_to_files(chunks)
    print(f"💾 保存されたファイル: {len(saved_files)}件")
    
    # チャンクの読み込みテスト
    loaded_chunks = splitter.load_chunks_from_files("tmp/context_chunks")
    print(f"📖 読み込まれたチャンク: {len(loaded_chunks)}件")


if __name__ == "__main__":
    main()