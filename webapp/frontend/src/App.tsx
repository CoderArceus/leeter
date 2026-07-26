import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Workspace } from "./components/Workspace";

function App() {
  return (
    <Router>
      <div className="flex h-screen bg-background text-foreground overflow-hidden">
        <Routes>
          <Route path="/" element={<Workspace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
