export function normalizeUtc(n: number) {
    // clamp and round to 0.5
    const clamped = Math.max(-12, Math.min(14, n));
    return Math.round(clamped * 2) / 2;
}

export function validateLight(d: number, m: number, l: number) {
    return d < m && m < l;
}

export function parseIni(text: string) {
    const out: Record<string, string> = {};
    const lines = text.split(/\r?\n/);
    for (const raw of lines) {
        const line = raw.trim();
        if (!line || line.startsWith('#') || line.startsWith('[')) continue;
        const i = line.indexOf('=');
        if (i > 0) {
            const k = line.slice(0, i).trim();
            const v = line.slice(i + 1).trim();
            out[k] = v;
        }
    }
    return out;
}

export function serializeIni(obj: Record<string, any>) {
    const lines: string[] = ['[SETTINGS]'];
    for (const k of Object.keys(obj)) {
        lines.push(`${k} = ${obj[k]}`);
    }
    return lines.join('\n');
}

export function validateConfigModel(model: any) {
    const errors: any = {};
    const utc = Number(model.UTC_OFFSET);
    if (Number.isNaN(utc) || normalizeUtc(utc) !== utc) errors.UTC_OFFSET = 'Must be step of 0.5 between -12.0 and 14.0';
    const dark = Number(model.HANGAR_DARK);
    const dim = Number(model.HANGAR_DIM);
    const lit = Number(model.HANGAR_LIT);
    if (!(dark < dim && dim < lit)) errors.LIGHT_THRESHOLDS = 'HANGAR_DARK < HANGAR_DIM < HANGAR_LIT';
    return errors;
}
