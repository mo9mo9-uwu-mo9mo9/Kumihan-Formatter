#!/usr/bin/env python3
"""
Context Inheritance Manager for Gemini Capability Enhancement
タスク間コンテキスト継承・共有情報管理システム
"""

import json
import os
import hashlib
import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict, field
from enum import Enum
import threading
import weakref

class ContextScope(Enum):
    """コンテキストスコープ"""
    GLOBAL = "global"          # グローバル共有（全タスク）
    SESSION = "session"        # セッション共有（セッション内全タスク）
    TASK_GROUP = "task_group"  # タスクグループ共有（関連タスクのみ）
    PARENT_CHILD = "parent_child"  # 親子関係（直接依存のみ）
    TEMPORAL = "temporal"      # 一時的（次のタスクのみ）

class ContextType(Enum):
    """コンテキストタイプ"""
    IMPLEMENTATION_CONTEXT = "implementation"    # 実装コンテキスト
    DESIGN_PATTERN = "design_pattern"           # 設計パターン
    CODE_STANDARDS = "code_standards"           # コーディング標準
    ERROR_CONTEXT = "error_context"             # エラー文脈
    EXECUTION_STATE = "execution_state"         # 実行状態
    QUALITY_METRICS = "quality_metrics"         # 品質メトリクス
    LEARNING_FEEDBACK = "learning_feedback"     # 学習フィードバック

@dataclass
class ContextEntry:
    """コンテキスト エントリ"""
    entry_id: str
    context_type: ContextType
    scope: ContextScope
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: str
    expires_at: Optional[str] = None
    access_count: int = 0
    last_accessed: Optional[str] = None
    source_task_id: str = ""
    tags: List[str] = field(default_factory=list)
    priority: int = 5  # 1(高) - 10(低)

@dataclass
class InheritanceRule:
    """継承ルール"""
    rule_id: str
    source_pattern: str        # ソースタスクパターン
    target_pattern: str        # ターゲットタスクパターン
    context_types: List[ContextType]  # 継承するコンテキストタイプ
    scope_filter: List[ContextScope]  # スコープフィルター
    transformation_func: Optional[str] = None  # 変換関数名
    conditions: Dict[str, Any] = field(default_factory=dict)  # 継承条件
    priority: int = 5

class ContextInheritanceManager:
    """
    コンテキスト継承管理システム
    タスク間でのコンテキスト共有・継承・一貫性保持を管理
    """
    
    def __init__(self, storage_dir: str = "postbox/context/storage"):
        """
        初期化
        
        Args:
            storage_dir: コンテキスト保存ディレクトリ
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # メモリ内コンテキストストレージ
        self.context_store: Dict[str, ContextEntry] = {}
        self.inheritance_rules: Dict[str, InheritanceRule] = {}
        
        # スレッドセーフ用ロック
        self._lock = threading.RLock()
        
        # セッション・タスクグループ管理
        self.active_sessions: Dict[str, Set[str]] = {}  # session_id -> task_ids
        self.task_groups: Dict[str, Set[str]] = {}      # group_id -> task_ids
        self.task_hierarchy: Dict[str, str] = {}        # task_id -> parent_task_id
        
        # アクセス統計
        self.access_stats: Dict[str, Dict[str, int]] = {}
        
        # デフォルト継承ルール設定
        self._setup_default_inheritance_rules()
        
        # 永続化ファイルから復元
        self._load_persistent_storage()
        
        print("🧠 ContextInheritanceManager 初期化完了")
        print(f"📁 ストレージディレクトリ: {self.storage_dir}")
        print(f"📋 継承ルール: {len(self.inheritance_rules)}件")
    
    def register_task_context(self, task_id: str, task_data: Dict[str, Any],
                            session_id: Optional[str] = None,
                            parent_task_id: Optional[str] = None,
                            task_group_id: Optional[str] = None) -> None:
        """
        タスクコンテキストの登録
        
        Args:
            task_id: タスクID
            task_data: タスクデータ
            session_id: セッションID
            parent_task_id: 親タスクID
            task_group_id: タスクグループID
        """
        
        with self._lock:
            print(f"📝 タスクコンテキスト登録: {task_id}")
            
            # セッション・グループ・階層関係の登録
            if session_id:
                if session_id not in self.active_sessions:
                    self.active_sessions[session_id] = set()
                self.active_sessions[session_id].add(task_id)
            
            if task_group_id:
                if task_group_id not in self.task_groups:
                    self.task_groups[task_group_id] = set()
                self.task_groups[task_group_id].add(task_id)
            
            if parent_task_id:
                self.task_hierarchy[task_id] = parent_task_id
            
            # タスクから基本コンテキストを抽出・登録
            self._extract_and_store_task_context(task_id, task_data)
            
            # 継承対象コンテキストの取得・適用
            inherited_contexts = self._get_inherited_contexts(task_id, task_data)
            for context in inherited_contexts:
                self._store_context_entry(context)
            
            print(f"✅ 登録完了: コンテキスト{len(inherited_contexts)}件継承")
    
    def get_task_context(self, task_id: str, context_types: Optional[List[ContextType]] = None,
                        include_inherited: bool = True) -> List[ContextEntry]:
        """
        タスクコンテキストの取得
        
        Args:
            task_id: タスクID
            context_types: 取得するコンテキストタイプ（Noneで全タイプ）
            include_inherited: 継承コンテキストを含むか
            
        Returns:
            コンテキストエントリリスト
        """
        
        with self._lock:
            contexts = []
            
            # 直接関連するコンテキスト
            for entry in self.context_store.values():
                if self._is_context_available_for_task(entry, task_id):
                    if context_types is None or entry.context_type in context_types:
                        # アクセス統計更新
                        self._update_access_stats(entry.entry_id, task_id)
                        contexts.append(entry)
            
            # 継承コンテキスト
            if include_inherited:
                parent_contexts = self._get_parent_contexts(task_id)
                for context in parent_contexts:
                    if context_types is None or context.context_type in context_types:
                        contexts.append(context)
            
            # 優先度・関連性でソート
            contexts.sort(key=lambda x: (x.priority, -x.access_count, x.created_at))
            
            print(f"📖 コンテキスト取得: {task_id} -> {len(contexts)}件")
            return contexts
    
    def store_context(self, task_id: str, context_type: ContextType,
                     content: Dict[str, Any], scope: ContextScope = ContextScope.SESSION,
                     metadata: Optional[Dict[str, Any]] = None,
                     tags: Optional[List[str]] = None,
                     priority: int = 5,
                     ttl_minutes: Optional[int] = None) -> str:
        """
        コンテキストの保存
        
        Args:
            task_id: ソースタスクID
            context_type: コンテキストタイプ
            content: コンテキスト内容
            scope: スコープ
            metadata: メタデータ
            tags: タグ
            priority: 優先度
            ttl_minutes: 生存時間（分）
            
        Returns:
            コンテキストエントリID
        """
        
        with self._lock:
            # エントリID生成
            content_hash = hashlib.md5(
                json.dumps(content, sort_keys=True).encode()
            ).hexdigest()[:8]
            entry_id = f"{context_type.value}_{task_id}_{content_hash}"
            
            # 有効期限設定
            expires_at = None
            if ttl_minutes:
                expires_at = (
                    datetime.datetime.now() + datetime.timedelta(minutes=ttl_minutes)
                ).isoformat()
            
            # コンテキストエントリ作成
            entry = ContextEntry(
                entry_id=entry_id,
                context_type=context_type,
                scope=scope,
                content=content,
                metadata=metadata or {},
                created_at=datetime.datetime.now().isoformat(),
                expires_at=expires_at,
                source_task_id=task_id,
                tags=tags or [],
                priority=priority
            )
            
            # ストレージに保存
            self._store_context_entry(entry)
            
            print(f"💾 コンテキスト保存: {entry_id} (スコープ: {scope.value})")
            return entry_id
    
    def update_context(self, entry_id: str, content: Optional[Dict[str, Any]] = None,
                      metadata: Optional[Dict[str, Any]] = None,
                      tags: Optional[List[str]] = None) -> bool:
        """
        コンテキストの更新
        
        Args:
            entry_id: エントリID
            content: 更新する内容
            metadata: 更新するメタデータ
            tags: 更新するタグ
            
        Returns:
            更新成功可否
        """
        
        with self._lock:
            if entry_id not in self.context_store:
                return False
            
            entry = self.context_store[entry_id]
            
            if content is not None:
                entry.content.update(content)
            if metadata is not None:
                entry.metadata.update(metadata)
            if tags is not None:
                entry.tags = tags
            
            # 永続化
            self._save_context_to_file(entry)
            
            print(f"🔄 コンテキスト更新: {entry_id}")
            return True
    
    def delete_context(self, entry_id: str) -> bool:
        """
        コンテキストの削除
        
        Args:
            entry_id: エントリID
            
        Returns:
            削除成功可否
        """
        
        with self._lock:
            if entry_id not in self.context_store:
                return False
            
            del self.context_store[entry_id]
            
            # ファイル削除
            file_path = self.storage_dir / f"{entry_id}.json"
            if file_path.exists():
                file_path.unlink()
            
            print(f"🗑️ コンテキスト削除: {entry_id}")
            return True
    
    def search_contexts(self, query: str, context_types: Optional[List[ContextType]] = None,
                       scopes: Optional[List[ContextScope]] = None,
                       tags: Optional[List[str]] = None,
                       limit: int = 10) -> List[ContextEntry]:
        """
        コンテキスト検索
        
        Args:
            query: 検索クエリ
            context_types: コンテキストタイプフィルター
            scopes: スコープフィルター  
            tags: タグフィルター
            limit: 結果上限数
            
        Returns:
            マッチするコンテキストエントリリスト
        """
        
        with self._lock:
            results = []
            query_lower = query.lower()
            
            for entry in self.context_store.values():
                # 期限切れチェック
                if self._is_context_expired(entry):
                    continue
                
                # フィルター適用
                if context_types and entry.context_type not in context_types:
                    continue
                if scopes and entry.scope not in scopes:
                    continue
                if tags and not any(tag in entry.tags for tag in tags):
                    continue
                
                # コンテンツ検索
                content_str = json.dumps(entry.content, ensure_ascii=False).lower()
                if query_lower in content_str or query_lower in entry.entry_id.lower():
                    results.append(entry)
                
                if len(results) >= limit:
                    break
            
            # 関連度でソート（アクセス数・優先度・作成日時）
            results.sort(key=lambda x: (-x.access_count, x.priority, x.created_at))
            
            return results
    
    def create_inheritance_rule(self, rule_id: str, source_pattern: str,
                              target_pattern: str, context_types: List[ContextType],
                              scope_filter: Optional[List[ContextScope]] = None,
                              conditions: Optional[Dict[str, Any]] = None,
                              priority: int = 5) -> None:
        """
        継承ルールの作成
        
        Args:
            rule_id: ルールID
            source_pattern: ソースタスクパターン（正規表現）
            target_pattern: ターゲットタスクパターン（正規表現）
            context_types: 継承対象コンテキストタイプ
            scope_filter: スコープフィルター
            conditions: 継承条件
            priority: ルール優先度
        """
        
        rule = InheritanceRule(
            rule_id=rule_id,
            source_pattern=source_pattern,
            target_pattern=target_pattern,
            context_types=context_types,
            scope_filter=scope_filter or list(ContextScope),
            conditions=conditions or {},
            priority=priority
        )
        
        self.inheritance_rules[rule_id] = rule
        self._save_inheritance_rules()
        
        print(f"📋 継承ルール作成: {rule_id}")
    
    def get_context_statistics(self) -> Dict[str, Any]:
        """コンテキスト統計情報取得"""
        
        with self._lock:
            stats = {
                "total_contexts": len(self.context_store),
                "context_types": {},
                "scopes": {},
                "active_sessions": len(self.active_sessions),
                "task_groups": len(self.task_groups),
                "inheritance_rules": len(self.inheritance_rules),
                "access_stats": dict(self.access_stats),
                "storage_size_mb": self._calculate_storage_size()
            }
            
            # タイプ別統計
            for entry in self.context_store.values():
                type_name = entry.context_type.value
                scope_name = entry.scope.value
                
                stats["context_types"][type_name] = stats["context_types"].get(type_name, 0) + 1
                stats["scopes"][scope_name] = stats["scopes"].get(scope_name, 0) + 1
            
            return stats
    
    def cleanup_expired_contexts(self) -> int:
        """期限切れコンテキストの削除"""
        
        with self._lock:
            expired_ids = []
            
            for entry_id, entry in self.context_store.items():
                if self._is_context_expired(entry):
                    expired_ids.append(entry_id)
            
            for entry_id in expired_ids:
                self.delete_context(entry_id)
            
            print(f"🧹 期限切れコンテキスト削除: {len(expired_ids)}件")
            return len(expired_ids)
    
    def optimize_storage(self) -> Dict[str, int]:
        """ストレージ最適化"""
        
        with self._lock:
            optimization_stats = {
                "contexts_removed": 0,
                "duplicates_merged": 0,
                "storage_saved_mb": 0
            }
            
            # 重複コンテキストの統合
            duplicates = self._find_duplicate_contexts()
            for duplicate_group in duplicates:
                if len(duplicate_group) > 1:
                    self._merge_duplicate_contexts(duplicate_group)
                    optimization_stats["duplicates_merged"] += len(duplicate_group) - 1
            
            # 低アクセスコンテキストの削除
            low_access_contexts = self._find_low_access_contexts()
            for context_id in low_access_contexts:
                self.delete_context(context_id)
                optimization_stats["contexts_removed"] += 1
            
            # ストレージサイズ再計算
            optimization_stats["storage_saved_mb"] = self._calculate_storage_size()
            
            return optimization_stats
    
    def export_contexts(self, export_path: str, 
                       context_types: Optional[List[ContextType]] = None) -> str:
        """コンテキストのエクスポート"""
        
        export_data = {
            "exported_at": datetime.datetime.now().isoformat(),
            "contexts": [],
            "inheritance_rules": [asdict(rule) for rule in self.inheritance_rules.values()],
            "statistics": self.get_context_statistics()
        }
        
        for entry in self.context_store.values():
            if context_types is None or entry.context_type in context_types:
                export_data["contexts"].append(asdict(entry))
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"📤 コンテキストエクスポート: {export_path} ({len(export_data['contexts'])}件)")
        return export_path
    
    def import_contexts(self, import_path: str, merge_strategy: str = "update") -> int:
        """コンテキストのインポート"""
        
        if not os.path.exists(import_path):
            return 0
        
        with open(import_path, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        imported_count = 0
        
        # コンテキストのインポート
        for context_data in import_data.get("contexts", []):
            entry = ContextEntry(**context_data)
            
            if merge_strategy == "update" or entry.entry_id not in self.context_store:
                self._store_context_entry(entry)
                imported_count += 1
        
        # 継承ルールのインポート
        for rule_data in import_data.get("inheritance_rules", []):
            rule = InheritanceRule(**rule_data)
            if merge_strategy == "update" or rule.rule_id not in self.inheritance_rules:
                self.inheritance_rules[rule.rule_id] = rule
        
        self._save_inheritance_rules()
        
        print(f"📥 コンテキストインポート: {imported_count}件")
        return imported_count
    
    def _extract_and_store_task_context(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """タスクからコンテキストを抽出・保存"""
        
        # 実装コンテキスト
        if task_data.get('type', '').endswith('_implementation'):
            implementation_context = {
                "task_type": task_data.get('type'),
                "target_files": task_data.get('target_files', []),
                "requirements": task_data.get('requirements', {}),
                "implementation_strategy": self._analyze_implementation_strategy(task_data)
            }
            
            self.store_context(
                task_id, ContextType.IMPLEMENTATION_CONTEXT, implementation_context,
                ContextScope.TASK_GROUP, tags=["implementation", "strategy"]
            )
        
        # エラーコンテキスト
        error_type = task_data.get('requirements', {}).get('error_type')
        if error_type:
            error_context = {
                "error_type": error_type,
                "target_files": task_data.get('target_files', []),
                "fix_patterns": self._get_error_fix_patterns(error_type),
                "common_solutions": self._get_common_solutions(error_type)
            }
            
            self.store_context(
                task_id, ContextType.ERROR_CONTEXT, error_context,
                ContextScope.SESSION, tags=["error", error_type]
            )
        
        # 品質メトリクス
        if 'quality' in task_data.get('requirements', {}):
            quality_context = {
                "quality_requirements": task_data['requirements']['quality'],
                "standards": self._get_quality_standards(),
                "validation_rules": self._get_validation_rules()
            }
            
            self.store_context(
                task_id, ContextType.QUALITY_METRICS, quality_context,
                ContextScope.GLOBAL, tags=["quality", "standards"]
            )
    
    def _get_inherited_contexts(self, task_id: str, 
                              task_data: Dict[str, Any]) -> List[ContextEntry]:
        """継承対象コンテキストの取得"""
        
        inherited_contexts = []
        
        # 継承ルールの適用
        for rule in sorted(self.inheritance_rules.values(), key=lambda x: x.priority):
            if self._rule_matches_task(rule, task_id, task_data):
                source_contexts = self._find_source_contexts(rule, task_data)
                for context in source_contexts:
                    inherited_context = self._transform_inherited_context(context, rule, task_id)
                    inherited_contexts.append(inherited_context)
        
        return inherited_contexts
    
    def _get_parent_contexts(self, task_id: str) -> List[ContextEntry]:
        """親タスクコンテキストの取得"""
        
        parent_contexts = []
        
        if task_id in self.task_hierarchy:
            parent_id = self.task_hierarchy[task_id]
            
            for entry in self.context_store.values():
                if (entry.source_task_id == parent_id and 
                    entry.scope in [ContextScope.PARENT_CHILD, ContextScope.TASK_GROUP]):
                    parent_contexts.append(entry)
        
        return parent_contexts
    
    def _is_context_available_for_task(self, entry: ContextEntry, task_id: str) -> bool:
        """タスクに対するコンテキストの可用性チェック"""
        
        # 期限切れチェック
        if self._is_context_expired(entry):
            return False
        
        # スコープ別可用性チェック
        if entry.scope == ContextScope.GLOBAL:
            return True
        elif entry.scope == ContextScope.SESSION:
            return self._is_same_session(entry.source_task_id, task_id)
        elif entry.scope == ContextScope.TASK_GROUP:
            return self._is_same_task_group(entry.source_task_id, task_id)
        elif entry.scope == ContextScope.PARENT_CHILD:
            return self._is_parent_child_relation(entry.source_task_id, task_id)
        elif entry.scope == ContextScope.TEMPORAL:
            return self._is_next_task(entry.source_task_id, task_id)
        
        return False
    
    def _is_context_expired(self, entry: ContextEntry) -> bool:
        """コンテキスト期限チェック"""
        
        if not entry.expires_at:
            return False
        
        expire_time = datetime.datetime.fromisoformat(entry.expires_at)
        return datetime.datetime.now() > expire_time
    
    def _is_same_session(self, task_id1: str, task_id2: str) -> bool:
        """同一セッションかチェック"""
        
        for session_tasks in self.active_sessions.values():
            if task_id1 in session_tasks and task_id2 in session_tasks:
                return True
        return False
    
    def _is_same_task_group(self, task_id1: str, task_id2: str) -> bool:
        """同一タスクグループかチェック"""
        
        for group_tasks in self.task_groups.values():
            if task_id1 in group_tasks and task_id2 in group_tasks:
                return True
        return False
    
    def _is_parent_child_relation(self, parent_id: str, child_id: str) -> bool:
        """親子関係かチェック"""
        
        return self.task_hierarchy.get(child_id) == parent_id
    
    def _is_next_task(self, prev_task_id: str, current_task_id: str) -> bool:
        """次タスクかチェック（簡易実装）"""
        
        # タイムスタンプベースの簡易判定
        # 実際には実行順序管理システムとの連携が必要
        return True  # 暫定的にTrue
    
    def _setup_default_inheritance_rules(self) -> None:
        """デフォルト継承ルールの設定"""
        
        # 実装系タスクの継承ルール
        self.create_inheritance_rule(
            "implementation_pattern_inheritance",
            r".*_implementation",
            r".*_implementation",
            [ContextType.IMPLEMENTATION_CONTEXT, ContextType.DESIGN_PATTERN],
            [ContextScope.TASK_GROUP, ContextScope.SESSION]
        )
        
        # エラー修正系タスクの継承ルール
        self.create_inheritance_rule(
            "error_context_inheritance", 
            r".*modification.*",
            r".*modification.*",
            [ContextType.ERROR_CONTEXT, ContextType.CODE_STANDARDS],
            [ContextScope.SESSION, ContextScope.GLOBAL]
        )
        
        # 品質系タスクの継承ルール
        self.create_inheritance_rule(
            "quality_standards_inheritance",
            r".*",
            r".*",
            [ContextType.QUALITY_METRICS, ContextType.CODE_STANDARDS],
            [ContextScope.GLOBAL]
        )
    
    def _store_context_entry(self, entry: ContextEntry) -> None:
        """コンテキストエントリの保存"""
        
        self.context_store[entry.entry_id] = entry
        self._save_context_to_file(entry)
    
    def _save_context_to_file(self, entry: ContextEntry) -> None:
        """コンテキストのファイル保存"""
        
        file_path = self.storage_dir / f"{entry.entry_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(entry), f, indent=2, ensure_ascii=False)
    
    def _load_persistent_storage(self) -> None:
        """永続化ストレージからの復元"""
        
        if not self.storage_dir.exists():
            return
        
        loaded_count = 0
        
        for file_path in self.storage_dir.glob("*.json"):
            if file_path.name.startswith("rules_"):
                continue  # ルールファイルは別途処理
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    entry_data = json.load(f)
                
                entry = ContextEntry(**entry_data)
                
                # 期限切れでなければロード
                if not self._is_context_expired(entry):
                    self.context_store[entry.entry_id] = entry
                    loaded_count += 1
                else:
                    # 期限切れファイルは削除
                    file_path.unlink()
            
            except Exception as e:
                print(f"⚠️ コンテキストファイル読み込みエラー {file_path}: {e}")
                continue
        
        # 継承ルール読み込み
        self._load_inheritance_rules()
        
        if loaded_count > 0:
            print(f"📖 永続化コンテキスト復元: {loaded_count}件")
    
    def _save_inheritance_rules(self) -> None:
        """継承ルールの保存"""
        
        rules_file = self.storage_dir / "rules_inheritance.json"
        rules_data = [asdict(rule) for rule in self.inheritance_rules.values()]
        
        with open(rules_file, 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, indent=2, ensure_ascii=False, default=self._json_serializer)
    
    def _load_inheritance_rules(self) -> None:
        """継承ルールの読み込み"""
        
        rules_file = self.storage_dir / "rules_inheritance.json"
        
        if not rules_file.exists():
            return
        
        try:
            with open(rules_file, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            
            for rule_dict in rules_data:
                # Enumの復元
                rule_dict['context_types'] = [ContextType(ct) for ct in rule_dict['context_types']]
                rule_dict['scope_filter'] = [ContextScope(sf) for sf in rule_dict['scope_filter']]
                
                rule = InheritanceRule(**rule_dict)
                self.inheritance_rules[rule.rule_id] = rule
            
            print(f"📋 継承ルール復元: {len(self.inheritance_rules)}件")
            
        except Exception as e:
            print(f"⚠️ 継承ルール読み込みエラー: {e}")
    
    def _update_access_stats(self, entry_id: str, task_id: str) -> None:
        """アクセス統計更新"""
        
        # エントリのアクセス統計
        if entry_id in self.context_store:
            entry = self.context_store[entry_id]
            entry.access_count += 1
            entry.last_accessed = datetime.datetime.now().isoformat()
        
        # 全体のアクセス統計
        if task_id not in self.access_stats:
            self.access_stats[task_id] = {}
        
        self.access_stats[task_id][entry_id] = self.access_stats[task_id].get(entry_id, 0) + 1
    
    def _calculate_storage_size(self) -> float:
        """ストレージサイズ計算（MB）"""
        
        total_size = 0
        
        if self.storage_dir.exists():
            for file_path in self.storage_dir.rglob("*.json"):
                total_size += file_path.stat().st_size
        
        return total_size / (1024 * 1024)  # MB
    
    def _find_duplicate_contexts(self) -> List[List[str]]:
        """重複コンテキストの検出"""
        
        content_hashes = {}
        
        for entry_id, entry in self.context_store.items():
            content_hash = hashlib.md5(
                json.dumps(entry.content, sort_keys=True).encode()
            ).hexdigest()
            
            if content_hash not in content_hashes:
                content_hashes[content_hash] = []
            content_hashes[content_hash].append(entry_id)
        
        return [group for group in content_hashes.values() if len(group) > 1]
    
    def _merge_duplicate_contexts(self, duplicate_ids: List[str]) -> None:
        """重複コンテキストの統合"""
        
        if len(duplicate_ids) <= 1:
            return
        
        # 最も新しいエントリを残す
        entries = [self.context_store[eid] for eid in duplicate_ids if eid in self.context_store]
        if not entries:
            return
        
        entries.sort(key=lambda x: x.created_at, reverse=True)
        keep_entry = entries[0]
        
        # アクセス数を統合
        total_access = sum(e.access_count for e in entries)
        keep_entry.access_count = total_access
        
        # 重複を削除
        for entry in entries[1:]:
            self.delete_context(entry.entry_id)
    
    def _find_low_access_contexts(self, threshold: int = 0) -> List[str]:
        """低アクセスコンテキストの検出"""
        
        low_access = []
        
        for entry_id, entry in self.context_store.items():
            if entry.access_count <= threshold and entry.scope != ContextScope.GLOBAL:
                # 作成から一定期間経過したもののみ対象
                created_time = datetime.datetime.fromisoformat(entry.created_at)
                if (datetime.datetime.now() - created_time).days >= 7:
                    low_access.append(entry_id)
        
        return low_access
    
    def _analyze_implementation_strategy(self, task_data: Dict[str, Any]) -> str:
        """実装戦略分析"""
        
        task_type = task_data.get('type', '')
        
        if task_type == 'new_implementation':
            return 'create_from_template'
        elif task_type == 'hybrid_implementation':
            return 'extend_existing'
        elif task_type == 'new_feature_development':
            return 'feature_driven'
        else:
            return 'generic'
    
    def _get_error_fix_patterns(self, error_type: str) -> List[str]:
        """エラー修正パターンの取得"""
        
        patterns = {
            'no-untyped-def': [
                'add_return_type_annotation',
                'add_parameter_type_annotation', 
                'add_typing_import'
            ],
            'no-untyped-call': [
                'add_type_ignore_comment',
                'add_stub_annotation',
                'refactor_call_site'
            ]
        }
        
        return patterns.get(error_type, ['generic_fix'])
    
    def _get_common_solutions(self, error_type: str) -> List[str]:
        """一般的な解決策の取得"""
        
        solutions = {
            'no-untyped-def': [
                'Use -> None for void functions',
                'Use -> Any for unknown return types',
                'Add from typing import Any if needed'
            ],
            'no-untyped-call': [
                'Add # type: ignore comment',
                'Create stub files for external libraries',
                'Use cast() for type conversion'
            ]
        }
        
        return solutions.get(error_type, ['Check documentation'])
    
    def _get_quality_standards(self) -> Dict[str, Any]:
        """品質標準の取得"""
        
        return {
            'mypy_strict': True,
            'code_coverage_min': 80,
            'max_complexity': 10,
            'docstring_required': True,
            'typing_required': True
        }
    
    def _get_validation_rules(self) -> List[str]:
        """検証ルールの取得"""
        
        return [
            'syntax_check',
            'type_check',
            'lint_check',
            'test_execution',
            'security_scan'
        ]
    
    def _rule_matches_task(self, rule: InheritanceRule, task_id: str, 
                          task_data: Dict[str, Any]) -> bool:
        """継承ルールのタスクマッチング"""
        
        import re
        
        # パターンマッチング
        if not re.match(rule.target_pattern, task_id):
            return False
        
        # 条件チェック
        for key, expected_value in rule.conditions.items():
            if key in task_data and task_data[key] != expected_value:
                return False
        
        return True
    
    def _find_source_contexts(self, rule: InheritanceRule, 
                            task_data: Dict[str, Any]) -> List[ContextEntry]:
        """ソースコンテキストの検索"""
        
        import re
        source_contexts = []
        
        for entry in self.context_store.values():
            # ソースパターンマッチング
            if re.match(rule.source_pattern, entry.source_task_id):
                # コンテキストタイプチェック
                if entry.context_type in rule.context_types:
                    # スコープフィルター
                    if entry.scope in rule.scope_filter:
                        source_contexts.append(entry)
        
        return source_contexts
    
    def _transform_inherited_context(self, context: ContextEntry, 
                                   rule: InheritanceRule, target_task_id: str) -> ContextEntry:
        """継承コンテキストの変換"""
        
        # 新しいエントリIDを生成
        inherited_id = f"inherited_{target_task_id}_{context.entry_id}"
        
        # コンテキストのクローン作成
        inherited_context = ContextEntry(
            entry_id=inherited_id,
            context_type=context.context_type,
            scope=context.scope,
            content=context.content.copy(),
            metadata=context.metadata.copy(),
            created_at=datetime.datetime.now().isoformat(),
            expires_at=context.expires_at,
            source_task_id=target_task_id,
            tags=context.tags + ["inherited"],
            priority=context.priority
        )
        
        # メタデータに継承情報を追加
        inherited_context.metadata['inherited_from'] = context.entry_id
        inherited_context.metadata['inheritance_rule'] = rule.rule_id
        
        return inherited_context


def main():
    """テスト実行"""
    
    manager = ContextInheritanceManager()
    
    print("🧪 ContextInheritanceManager テスト実行")
    
    # テストタスク登録
    task_id1 = "impl_001_base"
    task_data1 = {
        'type': 'new_implementation',
        'target_files': ['test_base.py'],
        'requirements': {
            'implementation_spec': {
                'template_type': 'class',
                'class_name': 'BaseImplementation'
            }
        }
    }
    
    manager.register_task_context(task_id1, task_data1, session_id="session_001")
    
    # コンテキスト保存テスト
    context_id = manager.store_context(
        task_id1, ContextType.IMPLEMENTATION_CONTEXT,
        {"strategy": "template_based", "patterns": ["factory", "observer"]},
        ContextScope.SESSION, tags=["implementation", "patterns"]
    )
    
    print(f"💾 保存されたコンテキスト: {context_id}")
    
    # 継承タスク登録
    task_id2 = "impl_002_derived"
    task_data2 = {
        'type': 'hybrid_implementation', 
        'target_files': ['test_derived.py'],
        'requirements': {
            'implementation_spec': {
                'template_type': 'class',
                'base_classes': ['BaseImplementation']
            }
        }
    }
    
    manager.register_task_context(task_id2, task_data2, session_id="session_001")
    
    # コンテキスト取得テスト
    contexts = manager.get_task_context(task_id2)
    print(f"📖 継承されたコンテキスト: {len(contexts)}件")
    
    for context in contexts:
        print(f"  - {context.entry_id} ({context.context_type.value})")
    
    # 統計表示
    stats = manager.get_context_statistics()
    print(f"\n📊 統計情報:")
    print(f"  総コンテキスト数: {stats['total_contexts']}")
    print(f"  継承ルール数: {stats['inheritance_rules']}")
    print(f"  ストレージサイズ: {stats['storage_size_mb']:.2f}MB")
    
    # 検索テスト
    search_results = manager.search_contexts("implementation")
    print(f"\n🔍 検索結果: {len(search_results)}件")
    
    # クリーンアップテスト
    cleaned = manager.cleanup_expired_contexts()
    print(f"🧹 クリーンアップ: {cleaned}件削除")


if __name__ == "__main__":
    main()