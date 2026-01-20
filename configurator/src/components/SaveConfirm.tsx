export default function SaveConfirm({ changes, onConfirm, onCancel }: { changes: string; onConfirm: () => void; onCancel: () => void; }) {
    return (
        <div className="save-confirm">
            <h3>Confirm Save</h3>
            <pre style={{ maxHeight: 200, overflow: 'auto' }}>{changes}</pre>
            <div>
                <button onClick={onConfirm}>Confirm</button>
                <button onClick={onCancel}>Cancel</button>
            </div>
        </div>
    );
}