import { useEffect, useState } from "react";
import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import CombinedCheck from "./pages/CombinedCheck.jsx";
import ImageModeration from "./pages/ImageModeration.jsx";
import TextModeration from "./pages/TextModeration.jsx";
import ReviewQueue from "./pages/ReviewQueue.jsx";
import Logs from "./pages/Logs.jsx";
import Settings from "./pages/Settings.jsx";
import { checkHealth } from "./api/client.js";
import { getLogs } from "./utils/storage.js";

export default function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const [logs, setLogs] = useState([]);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    setLogs(getLogs());
    checkHealth().then(setHealth).catch(() => setHealth({ pipeline_ready: false }));
  }, []);

  const props = { logs, onLogsChange: setLogs };

  return (
    <Layout activePage={activePage} onChangePage={setActivePage} health={health}>
      {activePage === "dashboard" && <Dashboard logs={logs} />}
      {activePage === "combined" && <CombinedCheck {...props} />}
      {activePage === "image" && <ImageModeration {...props} />}
      {activePage === "text" && <TextModeration {...props} />}
      {activePage === "review" && <ReviewQueue {...props} />}
      {activePage === "logs" && <Logs logs={logs} />}
      {activePage === "settings" && <Settings />}
    </Layout>
  );
}
