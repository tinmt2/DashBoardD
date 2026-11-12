
import React, { useState, useEffect } from "react";
import { ftelDvrApi } from "../api/ftelDvr";
import type { DvrItem } from "../api/ftelDvr";

const AllShop: React.FC = () => {
  const [data, setData] = useState<DvrItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadData = async (refresh: boolean = false) => {
    setLoading(true);
    setError("");
    try {
      const res = await ftelDvrApi.getData(refresh);
      if (res.success && res.data) {
        setData(res.data);
      } else {
        setError(res.message || "Failed to load data");
      }
    } catch (err: any) {
      setError(err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(false);
  }, []);

  const handleRowDoubleClick = async (item: DvrItem) => {
    try {
      const port = 81; // or from item if available
      await ftelDvrApi.autoLogin(item.ip, port, item.password);
    } catch (err: any) {
      console.error("AutoLogin failed:", err);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 p-6 overflow-hidden">
      <div className="flex items-center justify-between mb-6 shrink-0">
        <h1 className="text-xl font-semibold text-slate-100">All Shop</h1>
        <button
          onClick={() => loadData(true)}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          {loading ? "Loading..." : "Refresh Data"}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg shrink-0">
          {error}
        </div>
      )}

      <div className="flex-1 overflow-auto border border-slate-800/60 rounded-xl bg-slate-900/40">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="text-xs uppercase bg-slate-800/80 text-slate-400 sticky top-0 z-10 shadow-sm">
            <tr>
              <th className="px-4 py-3 font-medium">Mã Shop</th>
              <th className="px-4 py-3 font-medium">Tên Shop</th>
              <th className="px-4 py-3 font-medium">Vùng</th>
              <th className="px-4 py-3 font-medium">IP</th>
              <th className="px-4 py-3 font-medium">Tr?ng Thái DVR</th>
              <th className="px-4 py-3 font-medium">Tr?ng Thái Cam</th>
              <th className="px-4 py-3 font-medium">Ð? Tr?</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {data.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-slate-500 italic">
                  {loading ? "Loading..." : "No data available."}
                </td>
              </tr>
            ) : (
              data.map((item, idx) => (
                <tr
                  key={idx}
                  onDoubleClick={() => handleRowDoubleClick(item)}
                  className="hover:bg-slate-800/40 transition-colors cursor-pointer"
                >
                  <td className="px-4 py-3">{item.ma_shop}</td>
                  <td className="px-4 py-3 font-medium text-slate-200">{item.ten_shop}</td>
                  <td className="px-4 py-3">{item.vung}</td>
                  <td className="px-4 py-3 text-emerald-400">{item.ip}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${item.status === "OK" ? "bg-emerald-500/10 text-emerald-400" : item.status === "FAIL" ? "bg-red-500/10 text-red-400" : "bg-slate-800 text-slate-400"}`}>
                      {item.status || "N/A"}
                    </span>
                  </td>
                  <td className="px-4 py-3">{item.cam_status || "N/A"}</td>
                  <td className="px-4 py-3 font-mono">{item.latency || "-"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AllShop;

