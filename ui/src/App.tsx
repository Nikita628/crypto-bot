import React, { useEffect, useState } from "react";

function App() {
  const [state, setState] = useState<string | null>(null);

  useEffect(() => {
    fetch(process.env.REACT_APP_API_URL!)
      .then((res) => res.text())
      .then((text) => setState(text));
  }, []);

  return <div className="App">{state}</div>;
}

export default App;
