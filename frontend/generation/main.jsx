import { createRoot } from "react-dom/client";

import App from "./App";


const root = document.getElementById("generation-root");

if (root) {
  createRoot(root).render(<App />);
}
