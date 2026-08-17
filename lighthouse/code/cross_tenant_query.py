"""Azure Lighthouse 最終PJ（W7）— テナント横断クエリ E2E（Python + Azure Resource Graph）。

委任済みサブスク（W3 の main.bicep でオンボード）を、プロバイダーテナントから
1 回のクエリで横断的に調べる。W5 で学んだ Resource Graph / KQL を Python SDK で実装する。

3 つのデモクエリ:
  1) 見えているサブスクを tenantId 付きで一覧し、委任サブスク（tenantId != 自分）を印付け
  2) リソース件数を tenantId ごとに集計（どの顧客に何個あるか）
  3) HTTPS を強制していないストレージを全テナント横断で抽出（是正対象の棚卸し）

認証は DefaultAzureCredential（az login 済みでよい）。読み取り専用（作成・変更なし）。
参照：W5 §2（ARG/KQL・tenantId）、W1 §4（managedByTenants/homeTenantId）。
"""
from azure.identity import DefaultAzureCredential
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest, QueryRequestOptions

import config


def run_query(client: ResourceGraphClient, query: str, subscriptions=None) -> list[dict]:
    """KQL クエリを実行し、全ページを結合して返す（W5：skip_token でページング）。"""
    rows: list[dict] = []
    skip_token = None
    while True:
        options = QueryRequestOptions(skip_token=skip_token) if skip_token else QueryRequestOptions()
        request = QueryRequest(query=query, subscriptions=subscriptions, options=options)
        response = client.resources(request)
        rows.extend(response.data or [])
        skip_token = response.skip_token
        if not skip_token:
            break
    return rows


def _print_table(rows: list[dict], columns: list[str]) -> None:
    if not rows:
        print("  （0 件）")
        return
    widths = {c: max(len(c), *(len(str(r.get(c, ""))) for r in rows)) for c in columns}
    header = "  " + " | ".join(c.ljust(widths[c]) for c in columns)
    print(header)
    print("  " + "-+-".join("-" * widths[c] for c in columns))
    for r in rows:
        print("  " + " | ".join(str(r.get(c, "")).ljust(widths[c]) for c in columns))


def main() -> None:
    credential = DefaultAzureCredential()
    client = ResourceGraphClient(credential)
    subs = config.SUBSCRIPTIONS
    managing = config.MANAGING_TENANT_ID

    print("=" * 72)
    print("Azure Lighthouse テナント横断クエリ（W7）")
    print(f"  対象サブスク: {'アクセス可能な全て（委任含む）' if subs is None else subs}")
    print(f"  プロバイダーテナント: {managing or '(未設定：tenantId の違いのみ表示)'}")
    print("=" * 72)

    # --- 1) サブスク一覧（委任サブスクを印付け） -------------------------------
    print("\n[1] 見えているサブスクリプション（tenantId 付き）")
    subs_rows = run_query(
        client,
        "ResourceContainers "
        "| where type == 'microsoft.resources/subscriptions' "
        "| project name, subscriptionId, tenantId",
        subs,
    )
    for r in subs_rows:
        # 委任サブスク＝tenantId が自分（プロバイダー）と異なるもの（W5 §2-4）
        r["delegated"] = "◎ 委任" if (managing and r.get("tenantId") != managing) else ""
    _print_table(subs_rows, ["name", "subscriptionId", "tenantId", "delegated"])

    # --- 2) tenantId ごとのリソース件数 --------------------------------------
    print("\n[2] リソース件数（tenantId ごとに集計）")
    by_tenant = run_query(
        client,
        "Resources "
        "| summarize count() by tenantId "
        "| order by count_ desc",
        subs,
    )
    _print_table(by_tenant, ["tenantId", "count_"])

    # --- 3) HTTPS 未強制ストレージを横断抽出（是正候補） ----------------------
    print("\n[3] HTTPS を強制していないストレージ（全テナント横断）")
    insecure = run_query(
        client,
        "Resources "
        "| where type =~ 'Microsoft.Storage/storageAccounts' "
        "| where properties.supportsHttpsTrafficOnly == false "
        "| project name, resourceGroup, subscriptionId, tenantId",
        subs,
    )
    _print_table(insecure, ["name", "resourceGroup", "subscriptionId", "tenantId"])
    print(f"\n  → 是正候補: {len(insecure)} 件（W5 §3：Policy で HTTPS 強制につなげる）")
    print("\n完了。（読み取りのみ・作成物なし）")


if __name__ == "__main__":
    main()
