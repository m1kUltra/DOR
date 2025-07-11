import React, { useState, useEffect } from "react";

export default function Editor() {
  const [tables, setTables] = useState([]);
  const [selectedTable, setSelectedTable] = useState(null);
  const [rows, setRows] = useState([]);
  const [editedRows, setEditedRows] = useState({});

  useEffect(() => {
    window.api.getTables().then(setTables);
  }, []);

  const loadTable = async (tableName) => {
    const data = await window.api.getTableData(tableName);
    setSelectedTable(tableName);
    setRows(data);
    setEditedRows({});
  };

  const handleEdit = (rowIndex, colKey, newValue) => {
    setEditedRows((prev) => ({
      ...prev,
      [rowIndex]: {
        ...prev[rowIndex],
        [colKey]: newValue,
        id: rows[rowIndex].id,
      },
    }));
  };

  const saveChanges = async () => {
    for (const index in editedRows) {
      const updatedRow = editedRows[index];
      await window.api.updateRow(selectedTable, updatedRow);
    }
    loadTable(selectedTable);
  };

  return (
    <div className="screen">
      <h2>🛠️ SQLite Editor</h2>

      <div>
        <select onChange={(e) => loadTable(e.target.value)}>
          <option>Select Table</option>
          {tables.map((table) => (
            <option key={table}>{table}</option>
          ))}
        </select>
      </div>

      <table>
        <thead>
          <tr>
            {rows[0] &&
              Object.keys(rows[0]).map((key) => <th key={key}>{key}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {Object.entries(row).map(([key, value]) => (
                <td key={key}>
                  <input
                    value={
                      editedRows[i]?.[key] !== undefined
                        ? editedRows[i][key]
                        : value
                    }
                    onChange={(e) => handleEdit(i, key, e.target.value)}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {Object.keys(editedRows).length > 0 && (
        <button onClick={saveChanges}>💾 Save Changes</button>
      )}
    </div>
  );
}
