/**
 * Browser API polyfills for Node.js.
 *
 * The @akmf/ksef-fe-invoice-converter library uses FileReader (browser API)
 * to parse XML files. Node.js 22 has global File and Blob but not FileReader.
 * This polyfill provides a minimal FileReader implementation using Blob.text().
 */

if (typeof globalThis.FileReader === 'undefined') {
  class NodeFileReader extends EventTarget {
    result: string | ArrayBuffer | null = null;
    readyState = 0;
    error: DOMException | null = null;
    onload: ((this: FileReader, ev: ProgressEvent<FileReader>) => void) | null = null;
    onerror: ((this: FileReader, ev: ProgressEvent<FileReader>) => void) | null = null;
    onloadend: ((this: FileReader, ev: ProgressEvent<FileReader>) => void) | null = null;
    onloadstart: ((this: FileReader, ev: ProgressEvent<FileReader>) => void) | null = null;
    onprogress: ((this: FileReader, ev: ProgressEvent<FileReader>) => void) | null = null;
    onabort: ((this: FileReader, ev: ProgressEvent<FileReader>) => void) | null = null;

    readAsText(blob: Blob) {
      blob.text().then((text) => {
        this.result = text;
        this.readyState = 2;
        const event = new Event('load') as unknown as ProgressEvent<FileReader>;
        Object.defineProperty(event, 'target', { value: { result: text } });
        if (this.onload) this.onload.call(this as unknown as FileReader, event);
      }).catch((err) => {
        this.error = err;
        const event = new Event('error') as unknown as ProgressEvent<FileReader>;
        if (this.onerror) this.onerror.call(this as unknown as FileReader, event);
      });
    }

    readAsArrayBuffer(blob: Blob) {
      blob.arrayBuffer().then((ab) => {
        this.result = ab;
        this.readyState = 2;
        const event = new Event('load') as unknown as ProgressEvent<FileReader>;
        Object.defineProperty(event, 'target', { value: { result: ab } });
        if (this.onload) this.onload.call(this as unknown as FileReader, event);
      }).catch((err) => {
        this.error = err;
        const event = new Event('error') as unknown as ProgressEvent<FileReader>;
        if (this.onerror) this.onerror.call(this as unknown as FileReader, event);
      });
    }

    readAsDataURL(_blob: Blob) {
      throw new Error('readAsDataURL not implemented in polyfill');
    }

    readAsBinaryString(_blob: Blob) {
      throw new Error('readAsBinaryString not implemented in polyfill');
    }

    abort() {
      // noop
    }

    static readonly EMPTY = 0;
    static readonly LOADING = 1;
    static readonly DONE = 2;

    readonly EMPTY = 0;
    readonly LOADING = 1;
    readonly DONE = 2;
  }

  (globalThis as Record<string, unknown>).FileReader = NodeFileReader;
}
