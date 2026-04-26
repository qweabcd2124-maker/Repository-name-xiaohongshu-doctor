/**
 * 浏览器端本地诊断历史（IndexedDB）。
 * 数据仅保存在本机，不上传服务器；清除站点数据或换浏览器后需自行备份。
 *
 * - 每条诊断完整存一份。
 * - 主键为 `local-*`（及迁移遗留的 `legacy-*`）。
 */
import type { DiagnoseResult } from "./api";

const DB_NAME = "xiaohongshu-doctor_local_memory";
const DB_VERSION = 1;
const STORE = "diagnoses";

export interface LocalDiagnosisRecord {
  /** 主键：local-${uuid} 或迁移遗留 id */
  id: string;
  /** 保留字段；纯本地模式下始终为 null */
  serverId: string | null;
  title: string;
  category: string;
  overall_score: number;
  grade: string;
  createdAt: number;
  report: DiagnoseResult;
  params: Record<string, unknown>;
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onerror = () => reject(req.error ?? new Error("indexedDB open failed"));
    req.onsuccess = () => resolve(req.result);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: "id" });
      }
    };
  });
}

/**
 * 从旧版 localStorage 迁移至多 ~10 条简略记录（一次性）。
 */
export async function migrateLegacyLocalStorage(): Promise<void> {
  try {
    const raw = localStorage.getItem("xiaohongshu-doctor_history");
    if (!raw) return;
    const arr = JSON.parse(raw) as Array<{
      title: string;
      score: number;
      grade: string;
      category: string;
      date: number;
      report: DiagnoseResult;
      params?: Record<string, unknown>;
    }>;
    if (!Array.isArray(arr) || arr.length === 0) {
      localStorage.removeItem("xiaohongshu-doctor_history");
      return;
    }
    const db = await openDb();
    const tx = db.transaction(STORE, "readwrite");
    const os = tx.objectStore(STORE);
    for (const h of arr) {
      const id = `legacy-${h.date}-${Math.random().toString(36).slice(2, 10)}`;
      os.put({
        id,
        serverId: null,
        title: h.title,
        category: h.category,
        overall_score: h.score,
        grade: h.grade,
        createdAt: h.date,
        report: h.report,
        params: h.params ?? {},
      } satisfies LocalDiagnosisRecord);
    }
    await new Promise<void>((res, rej) => {
      tx.oncomplete = () => res();
      tx.onerror = () => rej(tx.error ?? new Error("tx failed"));
    });
    localStorage.removeItem("xiaohongshu-doctor_history");
  } catch {
    /* 迁移失败不阻塞主流程 */
  }
}

export async function putLocalDiagnosis(rec: LocalDiagnosisRecord): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error ?? new Error("put failed"));
    tx.objectStore(STORE).put(rec);
  });
}

export async function getLocalDiagnosis(id: string): Promise<LocalDiagnosisRecord | null> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const req = tx.objectStore(STORE).get(id);
    req.onsuccess = () => resolve((req.result as LocalDiagnosisRecord | undefined) ?? null);
    req.onerror = () => reject(req.error ?? new Error("get failed"));
  });
}

export async function listLocalDiagnoses(): Promise<LocalDiagnosisRecord[]> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const req = tx.objectStore(STORE).getAll();
    req.onsuccess = () => resolve((req.result as LocalDiagnosisRecord[]) ?? []);
    req.onerror = () => reject(req.error ?? new Error("getAll failed"));
  });
}

export async function deleteLocalDiagnosis(id: string): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error ?? new Error("delete failed"));
    tx.objectStore(STORE).delete(id);
  });
}

/** @returns 新的本地历史记录 id */
export function createLocalDiagnosisId(): string {
  return `local-${crypto.randomUUID()}`;
}

/**
 * @deprecated 请使用 {@link createLocalDiagnosisId}
 */
export function createPendingId(): string {
  return createLocalDiagnosisId();
}

export function localRecordToListItem(r: LocalDiagnosisRecord): import("./api").HistoryListItem {
  return {
    id: r.id,
    title: r.title,
    category: r.category,
    overall_score: r.overall_score,
    grade: r.grade,
    created_at: new Date(r.createdAt).toISOString(),
  };
}
