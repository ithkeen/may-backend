# Logging Decision Rules

## Log When

- A request, job, scheduler, or worker crosses a system boundary.
- A business state changes and the event is useful for operations or debugging.
- An external dependency call affects the workflow outcome.
- An error, retry, timeout, fallback, or degraded path is handled.
- Latency, queue depth, file size, batch size, retry count, or similar signal is abnormal or operationally useful.

## Do Not Log When

- The message only describes routine control flow, such as entering or leaving a function.
- The same fact is already captured by a nearby higher-level event.
- The code runs in a high-frequency loop without sampling or an abnormal condition.
- The same failure is already logged at the layer that handles it.
- The log would expose secrets, tokens, credentials, raw image data, or unnecessary sensitive data.
