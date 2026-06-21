<wizard-report>
# PostHog post-wizard report

The wizard has completed a full PostHog analytics integration for TaskFlow SaaS. The `posthog` Python SDK (v3+) was added to `requirements.txt` and installed. A `Posthog()` client instance is initialized at module level in `app.py` using `POSTHOG_API_KEY` and `POSTHOG_HOST` environment variables, with `enable_exception_autocapture=True` and an `atexit` shutdown handler to guarantee event delivery on process exit. Eight business events are captured across all key user and task flows, with user identity established on signup and login via `identify_context()` and `tag()` within request-scoped contexts. The `capture_exception()` call was added to the 500 error handler for server-side error tracking.

| Event name | Description | File |
|---|---|---|
| `user_signed_up` | Fired when a new user successfully creates an account via the registration form | `app.py` |
| `user_logged_in` | Fired when an existing user successfully authenticates with email and password | `app.py` |
| `user_logged_out` | Fired when an authenticated user explicitly logs out of the application | `app.py` |
| `dashboard_viewed` | Fired when an authenticated user visits the main dashboard — top of the task management funnel | `app.py` |
| `task_created` | Fired when a user successfully creates a new task | `app.py` |
| `task_updated` | Fired when a user saves edits to an existing task | `app.py` |
| `task_deleted` | Fired when a user permanently deletes one of their tasks | `app.py` |
| `task_status_toggled` | Fired when a user toggles a task between pending and completed status | `app.py` |

## Next steps

We've built some insights and a dashboard for you to keep an eye on user behavior, based on the events we just instrumented:

- **Dashboard**: [Analytics basics (wizard)](https://us.posthog.com/project/479470/dashboard/1741422)
- **New signups over time**: [https://us.posthog.com/project/479470/insights/LOSHNqvq](https://us.posthog.com/project/479470/insights/LOSHNqvq)
- **Daily active users**: [https://us.posthog.com/project/479470/insights/fS62euo5](https://us.posthog.com/project/479470/insights/fS62euo5)
- **Task creation vs completion rate**: [https://us.posthog.com/project/479470/insights/KV7lDwTn](https://us.posthog.com/project/479470/insights/KV7lDwTn)
- **Signup to first task funnel**: [https://us.posthog.com/project/479470/insights/Q7qE4d7M](https://us.posthog.com/project/479470/insights/Q7qE4d7M)
- **Task deletions — churn signal**: [https://us.posthog.com/project/479470/insights/Ab8ZIgsm](https://us.posthog.com/project/479470/insights/Ab8ZIgsm)

## Verify before merging

- [ ] Run a full production build and fix any lint errors introduced by the generated code.
- [ ] Run the test suite — call sites that were rewritten or instrumented may need updated mocks or fixtures.
- [ ] Add `POSTHOG_API_KEY` and `POSTHOG_HOST` to `.env.example` and any CI/CD or Azure App Service environment variable configuration so collaborators and the production deployment know what to set. (Already added to `.env.example`; confirm Azure portal settings are updated.)
- [ ] Confirm the returning-visitor path also calls `identify` — on login the integration sets user identity via `identify_context()`, but verify that sessions resumed from a Flask-Login cookie also resolve correctly in PostHog (the `user_loader` callback re-hydrates the user, but no PostHog event fires on cookie-based resumption, which is expected; confirm this matches your analytics requirements).

### Agent skill

We've left an agent skill folder in your project. You can use this context for further agent development when using Claude Code. This will help ensure the model provides the most up-to-date approaches for integrating PostHog.

</wizard-report>
