require('@testing-library/jest-dom');

// Polyfill TextEncoder/TextDecoder, which jsdom does not provide (undici needs them too).
const { TextEncoder, TextDecoder } = require('util');
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

// jsdom does not ship the WHATWG fetch primitives that React Router's loader/action
// navigation relies on. Polyfill them with undici (the same implementation Node uses),
// after providing the stream/blob globals undici itself depends on.
//
// Only fill GENUINE gaps (??=) — never overwrite a global jsdom already provides. In
// particular do NOT polyfill MessageChannel/MessagePort from node:worker_threads: React's
// scheduler picks up the global MessageChannel, and a Node worker_threads MessagePort stays
// ref'd, keeping the event loop alive so jest hangs on exit (CI) / force-kills the worker.
const { ReadableStream, WritableStream, TransformStream } = require('node:stream/web');
const { Blob } = require('node:buffer');
global.ReadableStream ??= ReadableStream;
global.WritableStream ??= WritableStream;
global.TransformStream ??= TransformStream;
global.Blob ??= Blob;
const { fetch, Request, Response, Headers, FormData } = require('undici');
global.fetch ??= fetch;
global.Request ??= Request;
global.Response ??= Response;
global.Headers ??= Headers;
global.FormData ??= FormData;

// jsdom does not implement these layout methods.
Element.prototype.scrollIntoView = jest.fn();
Element.prototype.scrollTo = jest.fn();
window.scrollTo = jest.fn();
