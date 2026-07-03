# AI 圆桌讨论 — ER 图

## Mermaid ER 图

```mermaid
erDiagram
    Session ||--o{ Expert : "包含"
    Session ||--o{ Transcript : "产生"
    Session ||--o{ Consensus : "总结出"
    Session ||--o{ Divergence : "记录"
    Expert ||--o{ Transcript : "发言"

    Session {
        string id PK "UUID"
        string topic "讨论话题"
        int expert_count "专家人数(1-10)"
        string status "状态枚举"
        string created_at "创建时间"
        string updated_at "更新时间"
    }

    Expert {
        string id PK "UUID"
        string session_id FK "所属会话"
        string name "姓名"
        string title "头衔"
        string stance "立场描述"
        string color "代表色HEX"
        string avatar_emoji "Emoji头像"
        int sort_order "排序"
        string created_at "创建时间"
    }

    Transcript {
        string id PK "UUID"
        string session_id FK "所属会话"
        string speaker_type "host|expert"
        string speaker_id "专家ID(FK,nullable)"
        string speaker_name "发言人姓名"
        string avatar_emoji "发言人头像"
        string content "发言内容"
        int sequence "全局序号"
        string created_at "发言时间"
    }

    Consensus {
        string id PK "UUID"
        string session_id FK "所属会话"
        string summary "共识描述"
        int sort_order "排序"
        string created_at "创建时间"
    }

    Divergence {
        string id PK "UUID"
        string session_id FK "所属会话"
        string description "分歧描述"
        string involved_experts "JSON专家ID数组"
        string side_a_expert "正方专家ID(FK)"
        string side_b_expert "反方专家ID(FK)"
        int sort_order "排序"
        string created_at "创建时间"
    }
```

## 实体列表（Markdown 表格 + 关系描述）

  实体列表

  ┌────────────┬────────────────────────┬─────────────────────────────────────────────────────────────────────────┐
  │    实体    │          描述          │                                核心字段                                 │
  ├────────────┼────────────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │ Session    │ 一次圆桌讨论会话       │ id, topic, expert_count, status, created_at                             │
  ├────────────┼────────────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │ Expert     │ 参与讨论的「虚拟专家」 │ id, session_id, name, title, stance, color, avatar_emoji                │
  ├────────────┼────────────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │ Transcript │ 单条发言记录           │ id, session_id, speaker_id, speaker_type, content, sequence, created_at │
  ├────────────┼────────────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │ Consensus  │ 达成的共识点           │ id, session_id, summary, created_at                                     │
  ├────────────┼────────────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │ Divergence │ 记录的分歧点           │ id, session_id, description, involved_experts, created_at               │
  └────────────┴────────────────────────┴─────────────────────────────────────────────────────────────────────────┘

  关系矩阵

  ┌─────────┬──────────┬────────────┬─────────────────────────────────────────────────────┐
  │  左端   │   关系   │    右端    │                        说明                         │
  ├─────────┼──────────┼────────────┼─────────────────────────────────────────────────────┤
  │ Session │ 1 ──── N │ Expert     │ 一个讨论会话有 N 位专家，Session 删除时级联清除专家 │
  ├─────────┼──────────┼────────────┼─────────────────────────────────────────────────────┤
  │ Session │ 1 ──── N │ Transcript │ 讨论过程产生 N 条发言记录，按 sequence 有序排列     │
  ├─────────┼──────────┼────────────┼─────────────────────────────────────────────────────┤
  │ Session │ 1 ──── N │ Consensus  │ 讨论结束后汇集 0~N 条共识要点                       │
  ├─────────┼──────────┼────────────┼─────────────────────────────────────────────────────┤
  │ Session │ 1 ──── N │ Divergence │ 讨论结束后汇集 0~N 条分歧要点                       │
  ├─────────┼──────────┼────────────┼─────────────────────────────────────────────────────┤
  │ Expert  │ 1 ──── N │ Transcript │ 每位专家发言 0~N 次；Host 发言时 speaker_id 为空    │
  └─────────┴──────────┴────────────┴─────────────────────────────────────────────────────┘

  关系图（文字版）

    ┌──────────┐          ┌────────────┐
    │ Consensus│◄─────────┤            │
    ├──────────┤ 0..N     │   Session  │
    │ summary  │          │            │
    └──────────┘          ├────────────┤
                          │ id         │
    ┌──────────┐          │ topic      │
    │Divergence│◄─────────┤ expert_cnt │
    ├──────────┤ 0..N     │ status     │
    │ desc     │          │ created_at │
    │ involved │          └─────┬──────┘
    └──────────┘                │
                       ┌────────┴────────┐
                       │                 │
                  ┌────▼─────┐   ┌──────▼──────┐
                  │  Expert  │    │ Transcript  │
                  ├──────────┤    ├─────────────┤
                  │ name     │    │ sequence    │
                  │ title    │    │ speaker_type│
                  │ stance   │    │ content     │
                  │ color    │◄───│ speaker_id  │
                  │ avatar   │ N  │ speaker_name│
                  └──────────┘    └─────────────┘
                  