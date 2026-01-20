import { useEffect, useState } from 'react';
import LightThresholds from '../components/LightThresholds';
import PinSelect from '../components/PinSelect';
import { normalizeUtc, parseIni, serializeIni, validateConfigModel } from '../lib/validation';

type Model = Record<string, any>;

export default function ConfigForm() {
    const [raw, setRaw] = useState('');
    const [model, setModel] = useState<Model>({});
    const [saving, setSaving] = useState(false);
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [message, setMessage] = useState<string | null>(null);
    const [senderConfirmed, setSenderConfirmed] = useState<Record<number, boolean>>({});
    const [senderOriginals, setSenderOriginals] = useState<Record<number, string>>({});
    const [configPath, setConfigPath] = useState<string | null>(null);
    const [debugParsed, setDebugParsed] = useState<Record<string, any> | null>(null);
    const [debugRawSenders, setDebugRawSenders] = useState<string | null>(null);
    const [clientLogs, setClientLogs] = useState<string[]>([]);

    function pushLog(msg: string) {
        try { console.debug('[ConfigForm]', msg); } catch (e) { }
        setClientLogs(prev => {
            const next = [...prev.slice(-80), msg]; // keep last 80
            return next;
        });
    }

    useEffect(() => {
        // Try multiple endpoints: backend first (dev), then same-origin
        const tryUrls = ['http://localhost:3000/api/config', '/api/config'];
        let finished = false
            ; (async () => {
                for (const url of tryUrls) {
                    try {
                        const r = await fetch(url);
                        if (!r.ok) continue;
                        const ct = r.headers.get('content-type') || '';
                        let resp: any;
                        if (ct.includes('application/json')) {
                            resp = await r.json();
                        } else {
                            // treat as plain text content
                            const text = await r.text();
                            resp = { content: text, path: null };
                        }
                        const t = resp.content || '';
                        // ignore HTML responses (Vite dev server index.html)
                        if (typeof t === 'string' && /<\!doctype|<html/i.test(t)) {
                            pushLog(`skipping HTML response from ${url}`);
                            continue;
                        }
                        const loadedPath = resp.path || null;
                        // debug to console for DevTools
                        try { console.debug('[ConfigForm] fetched', url, { path: loadedPath, contentPreview: (t || '').slice(0, 200) }); } catch (e) { }
                        pushLog(`fetched ${url} path=${loadedPath || '<null>'} contentPreview=${(t || '').slice(0, 120).replace(/\n/g, ' ')}`);
                        setRaw(t);
                        setConfigPath(loadedPath);
                        if (loadedPath) {
                            setMessage(`Loaded config from ${loadedPath}`);
                            setTimeout(() => setMessage(null), 2000);
                        }
                        const parsed = parseIni(t);
                        setDebugParsed(parsed);
                        try { console.debug('[ConfigForm] parsed INI map', parsed); } catch (e) { }
                        pushLog(`parsed INI map keys=${Object.keys(parsed).join(',')}`);
                        // determine raw allowed-senders string (try parsed map first, then regex fallback)
                        let rawSenders = parsed.ALLOWED_SENDERS;
                        setDebugRawSenders(rawSenders ?? null);
                        try { console.debug('[ConfigForm] raw ALLOWED_SENDERS', rawSenders); } catch (e) { }
                        pushLog(`raw ALLOWED_SENDERS=${rawSenders ?? '<null>'}`);
                        if (!rawSenders) {
                            const m = t.match(/^\s*ALLOWED_SENDERS\s*=\s*(.*)$/im);
                            rawSenders = m ? m[1].trim() : '';
                        }
                        // initialize model with parsed values or defaults
                        const initialSenders = rawSenders ? rawSenders.split(',').map((s: any) => String(s || '').trim()).filter(Boolean) : [];
                        setModel({
                            DEVICE_TYPE: parsed.DEVICE_TYPE || 'MeshCore',
                            UTC_OFFSET: parsed.UTC_OFFSET ? Number(parsed.UTC_OFFSET) : 8,
                            OLDEST_MESSAGE_TO_PROCESS: parsed.OLDEST_MESSAGE_TO_PROCESS || '60',
                            MAX_HEATER_TIME: parsed.MAX_HEATER_TIME || '90',
                            HEATER_PIN: parsed.HEATER_PIN ? Number(parsed.HEATER_PIN) : 22,
                            MQ2: parsed.MQ2 === 'True' || parsed.MQ2 === 'true' || parsed.MQ2 === 'True',
                            TEMP: parsed.TEMP === 'True' || parsed.TEMP === 'true',
                            LIGHT_SENSOR: parsed.LIGHT_SENSOR === 'True' || parsed.LIGHT_SENSOR === 'true',
                            HANGAR_DARK: parsed.HANGAR_DARK ? Number(parsed.HANGAR_DARK) : 20,
                            HANGAR_DIM: parsed.HANGAR_DIM ? Number(parsed.HANGAR_DIM) : 60,
                            HANGAR_LIT: parsed.HANGAR_LIT ? Number(parsed.HANGAR_LIT) : 90,
                            DISPLAY_ENABLED: parsed.DISPLAY_ENABLED === 'True' || parsed.DISPLAY_ENABLED === 'true',
                            TEST_MODE: parsed.TEST_MODE === 'True' || parsed.TEST_MODE === 'true',
                            ALLOWED_SENDERS: initialSenders
                        });
                        // initialize originals map for sender confirm state
                        const origMap: Record<number, string> = {};
                        initialSenders.forEach((v: string, i: number) => { origMap[i] = v; });
                        if (initialSenders.length === 0) origMap[0] = '';
                        setSenderOriginals(origMap);
                        finished = true;
                        break;
                    } catch (e) {
                        try { console.debug('[ConfigForm] fetch error for', url, e); } catch (err) { }
                        pushLog(`fetch error ${url} ${e}`);
                        // try next URL
                        continue;
                    }
                }
                if (!finished) {
                    console.error('[ConfigForm] Unable to load configuration from any endpoint');
                    pushLog('Unable to load configuration from any endpoint');
                    setMessage('Unable to load configuration');
                }
            })();
    }, []);

    function updateModel(partial: Partial<Model>) {
        const next = { ...model, ...partial };
        setModel(next);
        setErrors(validateConfigModel(next));
    }

    function onLightChange(d: number, m: number, l: number) {
        updateModel({ HANGAR_DARK: d, HANGAR_DIM: m, HANGAR_LIT: l });
    }

    function getPreviewText() {
        const obj: Record<string, any> = {
            DEVICE_TYPE: model.DEVICE_TYPE,
            UTC_OFFSET: model.UTC_OFFSET,
            OLDEST_MESSAGE_TO_PROCESS: model.OLDEST_MESSAGE_TO_PROCESS,
            MAX_HEATER_TIME: model.MAX_HEATER_TIME,
            HEATER_PIN: model.HEATER_PIN,
            MQ2: model.MQ2 ? 'True' : 'False',
            TEMP: model.TEMP ? 'True' : 'False',
            LIGHT_SENSOR: model.LIGHT_SENSOR ? 'True' : 'False',
            HANGAR_DARK: model.HANGAR_DARK,
            HANGAR_DIM: model.HANGAR_DIM,
            HANGAR_LIT: model.HANGAR_LIT,
            DISPLAY_ENABLED: model.DISPLAY_ENABLED ? 'True' : 'False',
            TEST_MODE: model.TEST_MODE ? 'True' : 'False',
            ALLOWED_SENDERS: (model.ALLOWED_SENDERS || []).join(', ')
        };
        return serializeIni(obj);
    }

    // overall form validity: no validation errors and required fields present
    const hasValue = (v: any) => v !== undefined && v !== null && String(v) !== '' && !(typeof v === 'number' && Number.isNaN(v));
    const requiredKeys = ['DEVICE_TYPE', 'UTC_OFFSET', 'OLDEST_MESSAGE_TO_PROCESS', 'MAX_HEATER_TIME', 'HEATER_PIN', 'HANGAR_DARK', 'HANGAR_DIM', 'HANGAR_LIT'];
    const requiredPresent = requiredKeys.every(k => hasValue((model as any)[k]));
    const hasSender = (model.ALLOWED_SENDERS || []).some((s: string) => String(s || '').trim());
    const formValid = Object.keys(errors || {}).length === 0 && requiredPresent && hasSender;

    async function onSaveStructured() {
        setErrors(validateConfigModel(model));
        const errs = validateConfigModel(model);
        if (Object.keys(errs).length) { setMessage('Fix validation errors'); return; }
        // normalize UTC
        model.UTC_OFFSET = normalizeUtc(Number(model.UTC_OFFSET));
        const obj: Record<string, any> = {
            DEVICE_TYPE: model.DEVICE_TYPE,
            UTC_OFFSET: model.UTC_OFFSET,
            OLDEST_MESSAGE_TO_PROCESS: model.OLDEST_MESSAGE_TO_PROCESS,
            MAX_HEATER_TIME: model.MAX_HEATER_TIME,
            HEATER_PIN: model.HEATER_PIN,
            MQ2: model.MQ2 ? 'True' : 'False',
            TEMP: model.TEMP ? 'True' : 'False',
            LIGHT_SENSOR: model.LIGHT_SENSOR ? 'True' : 'False',
            HANGAR_DARK: model.HANGAR_DARK,
            HANGAR_DIM: model.HANGAR_DIM,
            HANGAR_LIT: model.HANGAR_LIT,
            DISPLAY_ENABLED: model.DISPLAY_ENABLED ? 'True' : 'False',
            TEST_MODE: model.TEST_MODE ? 'True' : 'False',
            ALLOWED_SENDERS: (model.ALLOWED_SENDERS || []).join(', ')
        };
        const text = serializeIni(obj);
        setSaving(true);
        try {
            const res = await fetch('/api/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content: text, path: configPath }) });
            setMessage(res.ok ? 'Saved structured config' : 'Save failed');
            if (res.ok) {
                // sync originals to current senders after successful save
                const cur = (model.ALLOWED_SENDERS || []).slice();
                const newOrig: Record<number, string> = {};
                cur.forEach((v: string, i: number) => { newOrig[i] = String(v || '').trim(); });
                if (cur.length === 0) newOrig[0] = '';
                setSenderOriginals(newOrig);
            }
        } catch (e) {
            setMessage('Save failed');
        } finally { setSaving(false); }
    }

    // derive senders array for UI (always at least one entry shown)
    const senders = (model.ALLOWED_SENDERS && model.ALLOWED_SENDERS.length) ? model.ALLOWED_SENDERS : [''];
    const lastEmpty = !String(senders[senders.length - 1] ?? '').trim();

    return (
        <div className="config-form">

            <section className="config-section">
                <h3>Allowed Senders</h3>
                <div className="senders-list">
                    {senders.map((s: string, idx: number) => {
                        const isOnly = ((model.ALLOWED_SENDERS || []).length <= 1);
                        const showWarning = isOnly && (!s || !s.trim());
                        const confirmed = !!senderConfirmed[idx];
                        return (
                            <div key={idx} className={`sender-row ${showWarning ? 'sender-warning' : ''}`}>
                                <input
                                    className="sender-input"
                                    value={s}
                                    placeholder="e.g. +1234567890"
                                    onChange={e => {
                                        const arr = (model.ALLOWED_SENDERS || []).slice();
                                        // ensure at least one element exists
                                        if (!arr.length) arr.push('');
                                        arr[idx] = e.target.value;
                                        updateModel({ ALLOWED_SENDERS: arr });
                                        setSenderConfirmed(prev => ({ ...prev, [idx]: false }));
                                    }}
                                />
                                <div className="sender-actions">
                                    <button type="button" className="sender-confirm" onClick={() => {
                                        // mark confirmed briefly and update original value for this index
                                        const current = String(s || '').trim();
                                        setSenderOriginals(prev => ({ ...prev, [idx]: current }));
                                        setSenderConfirmed(prev => ({ ...prev, [idx]: true }));
                                        setTimeout(() => setSenderConfirmed(prev => ({ ...prev, [idx]: false })), 2000);
                                    }} disabled={!String(s).trim() || String(s || '').trim() === String(senderOriginals[idx] ?? '').trim()}>{confirmed ? 'Saved' : 'Confirm'}</button>
                                    <button type="button" onClick={() => {
                                        const arr = (model.ALLOWED_SENDERS || []).slice();
                                        const orig = { ...senderOriginals };
                                        if (arr.length <= 1) {
                                            // reset to single empty entry
                                            updateModel({ ALLOWED_SENDERS: [''] });
                                            setSenderOriginals({ 0: '' });
                                            return;
                                        }
                                        arr.splice(idx, 1);
                                        // adjust originals map (shift keys after removed index)
                                        const newOrig: Record<number, string> = {};
                                        arr.forEach((v: string, i: number) => { newOrig[i] = orig[i < idx ? i : i + 1] ?? v; });
                                        updateModel({ ALLOWED_SENDERS: arr });
                                        setSenderOriginals(newOrig);
                                    }} disabled={(model.ALLOWED_SENDERS || []).length <= 1}>Remove</button>
                                </div>
                            </div>
                        );
                    })}
                    <div style={{ marginTop: 8 }}>
                        <button type="button" className="sender-add" onClick={() => {
                            const arr = (model.ALLOWED_SENDERS || []).slice();
                            const orig = { ...senderOriginals };
                            arr.push('');
                            // add an empty original for the new index
                            const newIndex = arr.length - 1;
                            orig[newIndex] = '';
                            updateModel({ ALLOWED_SENDERS: arr });
                            setSenderOriginals(orig);
                        }} disabled={lastEmpty}>+ Add Sender</button>
                    </div>
                </div>
            </section>

            <section className="config-section">
                <h3>Device</h3>
                <label>Device Type
                    <select value={model.DEVICE_TYPE ?? 'MeshCore'} onChange={e => updateModel({ DEVICE_TYPE: e.target.value })}>
                        <option>MeshCore</option>
                        <option>Meshtastic</option>
                        <option>Sim800C</option>
                        <option>Test</option>
                    </select>
                </label>
            </section>

            <section className="config-section">
                <h3>Time / Scheduling</h3>
                <label>UTC Offset
                    <select value={String(model.UTC_OFFSET ?? 8)} onChange={e => updateModel({ UTC_OFFSET: Number(e.target.value) })}>
                        {Array.from({ length: ((14 - (-12)) * 2) + 1 }, (_, i) => -12 + i * 0.5).map(v => (
                            <option key={v} value={String(v)}>{v > 0 ? `+${v}` : String(v)}</option>
                        ))}
                    </select>
                    {errors.UTC_OFFSET && <div className="error">{errors.UTC_OFFSET}</div>}
                </label>
                <label>Oldest Message To Process
                    <select value={model.OLDEST_MESSAGE_TO_PROCESS ?? '60'} onChange={e => updateModel({ OLDEST_MESSAGE_TO_PROCESS: e.target.value })}>
                        {[1, 5, 10, 15, 30, 45, 60].map(n => <option key={n} value={String(n)}>{n}</option>)}
                    </select>
                </label>
            </section>

            <section className="config-section">
                <h3>Heater</h3>
                <label>Max Heater Time
                    <select value={model.MAX_HEATER_TIME ?? '90'} onChange={e => updateModel({ MAX_HEATER_TIME: e.target.value })}>
                        {[15, 30, 60, 90, 120, 150, 180].map(n => <option key={n} value={String(n)}>{n}</option>)}
                    </select>
                </label>
                <PinSelect value={model.HEATER_PIN} onChange={(v) => updateModel({ HEATER_PIN: v })} />
            </section>

            <section className="config-section sensors-list">
                <h3>Devices</h3>
                <div className="sensor-row">
                    <span className="sensor-name">MQ2</span>
                    <label className="sensor-toggle">
                        <input type="checkbox" checked={!!model.MQ2} onChange={e => updateModel({ MQ2: e.target.checked })} />
                        <span className="toggle-label">{model.MQ2 ? 'Enabled' : 'Off'}</span>
                    </label>
                </div>
                <div className="sensor-row">
                    <span className="sensor-name">Temperature Probe</span>
                    <label className="sensor-toggle">
                        <input type="checkbox" checked={!!model.TEMP} onChange={e => updateModel({ TEMP: e.target.checked })} />
                        <span className="toggle-label">{model.TEMP ? 'Enabled' : 'Off'}</span>
                    </label>
                </div>
                <div className="sensor-row">
                    <span className="sensor-name">Light Sensor</span>
                    <label className="sensor-toggle">
                        <input type="checkbox" checked={!!model.LIGHT_SENSOR} onChange={e => updateModel({ LIGHT_SENSOR: e.target.checked })} />
                        <span className="toggle-label">{model.LIGHT_SENSOR ? 'Enabled' : 'Off'}</span>
                    </label>
                </div>
                <div className="sensor-row">
                    <span className="sensor-name">Display</span>
                    <label className="sensor-toggle">
                        <input type="checkbox" checked={!!model.DISPLAY_ENABLED} onChange={e => updateModel({ DISPLAY_ENABLED: e.target.checked })} />
                        <span className="toggle-label">{model.DISPLAY_ENABLED ? 'Enabled' : 'Off'}</span>
                    </label>
                </div>
            </section>

            <section className="config-section">
                <h3>Light Thresholds</h3>
                <LightThresholds dark={model.HANGAR_DARK ?? 20} dim={model.HANGAR_DIM ?? 60} lit={model.HANGAR_LIT ?? 90} onChange={onLightChange} />
                {errors.LIGHT_THRESHOLDS && <div className="error">{errors.LIGHT_THRESHOLDS}</div>}
            </section>

            <section className="config-section sensors-list">
                <h3>Test Settings</h3>
                <div className="sensor-row">
                    <span className="sensor-name">Test Mode</span>
                    <label className="sensor-toggle">
                        <input type="checkbox" checked={!!model.TEST_MODE} onChange={e => updateModel({ TEST_MODE: e.target.checked })} />
                        <span className="toggle-label">{model.TEST_MODE ? 'Enabled' : 'Off'}</span>
                    </label>
                </div>
            </section>

            <section className="config-section actions-row">
                <div className="actions">
                    <button onClick={onSaveStructured} disabled={saving || !formValid}>{saving ? 'Saving...' : 'Save'}</button>
                </div>
            </section>

            <section className="config-section">
                <h3>Preview</h3>
                <textarea value={getPreviewText()} readOnly rows={10} />
                {configPath && <div style={{ marginTop: 8, fontSize: '0.85rem', color: '#666' }}>Loaded from: {configPath}</div>}
            </section>

            {/*
            <section className="config-section">
                <h3>Debug (parsing)</h3>
                <div style={{ fontSize: '0.85rem', color: '#444' }}>
                    <div>raw ALLOWED_SENDERS: {debugRawSenders ?? '<null>'}</div>
                    <pre style={{ whiteSpace: 'pre-wrap', maxHeight: 160, overflow: 'auto' }}>{debugParsed ? JSON.stringify(debugParsed, null, 2) : 'no parsed map'}</pre>
                </div>
            </section>
            */}
            {/*
            <section className="config-section">
                <h3>Client Logs</h3>
                <div style={{ fontSize: '0.8rem', color: '#333', maxHeight: 200, overflow: 'auto', background: '#fafafa', padding: 8, borderRadius: 6 }}>
                    {clientLogs.length === 0 ? <div style={{ color: '#888' }}>no logs yet</div> : clientLogs.map((l, i) => <div key={i}>{l}</div>)}
                </div>
            </section>
            */}

            {/*
            {message && <div className="message">{message}</div>}
            */}
        </div>
    );
}
