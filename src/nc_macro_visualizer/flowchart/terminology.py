from __future__ import annotations


SCHEMA_VERSION = "beginner-flow/v0.2"

ASSIGNMENT_TITLE = "値を入れる"
CALCULATION_TITLE = "値を計算する"
IF_GOTO_TITLE = "条件で分かれる"
IF_THEN_TITLE = "条件が合うと処理する"
IF_THEN_ELSE_TITLE = "条件で分かれる"
GOTO_TITLE = "指定した場所へ進む"
JUMP_IN_TITLE = "合流地点"
WHILE_TITLE = "条件の間くり返す"
CALL_TITLE = "別のプログラムを呼び出す"
PROGRAM_END_TITLE = "プログラムを終了する"
MACHINE_ACTION_TITLE = "機械を動かす"
PROCESS_TITLE = "処理する"
START_TITLE = "開始"
END_TITLE = "終了"
UNKNOWN_M_CODE_TITLE = "意味の確認が必要なMコード"
UNKNOWN_M_CODE_MESSAGE = "機械の説明書、PMC、ビルダー設定を確認してください。"
MACHINE_BEHAVIOR_DISCLAIMER = "本ツールは機械動作を保証しません。実機での実行前に必ず確認してください。"
CONDITIONAL_SUMMARY = "条件によって処理が変わります"
LOOP_SUMMARY = "条件の間、処理をくり返します"
UNKNOWN_M_CODE_CONFIRMATION_SUMMARY = "機械の説明書、PMC、ビルダー設定を確認してください"
PROGRAM_START_LABEL = "プログラム開始"
PROGRAM_END_LABEL = "プログラム終了"
PROGRAM_START_MARK = "▶"
PROGRAM_END_MARK = "■"

EDGE_LABELS = {
    "sequential": "次へ",
    "branch_true": "はい",
    "branch_false": "いいえ",
    "jump": "指定場所へ",
    "loop_body": "くり返す",
    "loop_exit": "終了",
    "call": "呼び出し",
}

STRUCTURED_SECTION_LABELS = {
    "sequence": "",
    "if_then": "もし～なら",
    "if_then_else": "もし～なら / そうでなければ",
    "while_loop": "～の間くり返し",
}

UNSTRUCTURED_JUMP_NOTE = "この箇所は構造化できないため、ジャンプとして表示しています"


def edge_label(kind: str) -> str:
    return EDGE_LABELS[kind]
