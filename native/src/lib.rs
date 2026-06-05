use pyo3::prelude::*;
use pyo3::types::PyBytes;
use serde_json::Value;

/// Sort keys recursively to ensure deterministic output matching orjson OPT_SORT_KEYS.
fn sort_value(v: Value) -> Value {
    match v {
        Value::Object(map) => {
            let mut sorted: serde_json::Map<String, Value> = serde_json::Map::new();
            let mut keys: Vec<String> = map.keys().cloned().collect();
            keys.sort();
            for key in keys {
                if let Some(val) = map.get(&key) {
                    sorted.insert(key, sort_value(val.clone()));
                }
            }
            Value::Object(sorted)
        }
        Value::Array(arr) => Value::Array(arr.into_iter().map(sort_value).collect()),
        other => other,
    }
}

/// Encode a Python object to JSON bytes with sorted keys.
#[pyfunction]
fn encode(py: Python<'_>, obj: &Bound<'_, PyAny>) -> PyResult<Py<PyBytes>> {
    let value: Value = pythonize::depythonize(obj)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let sorted = sort_value(value);
    let bytes = serde_json::to_vec(&sorted)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(PyBytes::new(py, &bytes).into())
}

/// Decode JSON bytes to a Python object.
#[pyfunction]
fn decode(py: Python<'_>, data: &[u8]) -> PyResult<Py<PyAny>> {
    let value: Value = serde_json::from_slice(data)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let obj: Bound<'_, PyAny> = pythonize::pythonize(py, &value)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(obj.unbind())
}

#[pymodule]
#[pyo3(name = "_native")]
fn graphql_mcp_native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", "0.1.0")?;
    m.add_function(wrap_pyfunction!(encode, m)?)?;
    m.add_function(wrap_pyfunction!(decode, m)?)?;
    Ok(())
}
