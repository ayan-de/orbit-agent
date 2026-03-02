# JIRA Integration Implementation Guide

**Scope**: JIRA ticket management integration
**Target**: User can connect Jira, list tickets, manage workflow
**Duration**: 2-3 weeks
**Last Updated**: 2026-03-01

---

## Overview

This guide focuses on building a complete JIRA integration for Orbit Agent:
- Connect to JIRA via API tokens
- List assigned tickets
- Get ticket details
- Transition ticket status
- Daily activity summaries
- Intent-based chat commands

---

## Phase 1: Database & Foundation (Days 1-2)

**Goal**: Set up database schema and foundation utilities.

### Day 1: Database Schema

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 1.1 | Generate database migration | `packages/bridge/migrations/` | ⬜ |
| 1.2 | Add Jira fields to User entity | `packages/bridge/src/infrastructure/database/entities/user.entity.ts` | ⬜ |
| 1.3 | Run database migration | `packages/bridge/` | ⬜ |
| 1.4 | Create token encryption utilities | `packages/bridge/src/infrastructure/security/token-encryption.util.ts` | ⬜ |
| 1.5 | Create type definitions | `packages/bridge/src/application/jira/types/jira.types.ts` | ⬜ |

### Day 2: Type Definitions & Tests

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 2.1 | Create unit tests for encryption | `packages/bridge/test/utils/token-encryption.util.spec.ts` | ⬜ |
| 2.2 | Verify type definitions compile | `packages/bridge/src/application/jira/types/jira.types.ts` | ⬜ |

---

## Phase 2: JIRA Service (Days 3-4)

**Goal**: Create JIRA service with full API integration.

### Day 3: JIRA HTTP Client

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 3.1 | Create JIRA HTTP client | `packages/bridge/src/application/jira/jira-client.service.ts` | ⬜ |
| 3.2 | Implement searchTickets method | `packages/bridge/src/application/jira/jira-client.service.ts` | ⬜ |
| 3.3 | Implement getIssueDetails method | `packages/bridge/src/application/jira/jira-client.service.ts` | ⬜ |
| 3.4 | Implement getTransitions method | `packages/bridge/src/application/jira/jira-client.service.ts` | ⬜ |
| 3.5 | Implement transitionIssue method | `packages/bridge/src/application/jira/jira-client.service.ts` | ⬜ |
| 3.6 | Implement addComment method | `packages/bridge/src/application/jira/jira-client.service.ts` | ⬜ |
| 3.7 | Implement getChangelog method | `packages/bridge/src/application/jira/jira-client.service.ts` | ⬜ |

### Day 4: JIRA Service

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 4.1 | Create JIRA service class | `packages/bridge/src/application/jira/jira.service.ts` | ⬜ |
| 4.2 | Implement connect method (with encryption) | `packages/bridge/src/application/jira/jira.service.ts` | ⬜ |
| 4.3 | Implement disconnect method | `packages/bridge/src/application/jira/jira.service.ts` | ⬜ |
| 4.4 | Implement getConnectionStatus method | `packages/bridge/src/application/jira/jira.service.ts` | ⬜ |
| 4.5 | Implement getAssignedTickets method | `packages/bridge/src/application/jira/jira.service.ts` | ⬜ |
| 4.6 | Implement getTicketDetails method | `packages/bridge/src/application/jira/jira.service.ts` | ⬜ |
| 4.7 | Implement transitionTicket method | `packages/bridge/src/application/jira/jira.service.ts` | ⬜ |
| 4.8 | Implement getDailyActivity method | `packages/bridge/src/application/jira/jira.service.ts` | ⬜ |
| 4.9 | Create unit tests for service | `packages/bridge/test/jira/jira.service.spec.ts` | ⬜ |

---

## Phase 3: Controller & DTOs (Day 5)

**Goal**: Create REST API endpoints for JIRA operations.

### Day 5: Controllers and DTOs

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 5.1 | Create JiraConnectDto | `packages/bridge/src/application/jira/dto/jira-connect.dto.ts` | ⬜ |
| 5.2 | Create TransitionTicketDto | `packages/bridge/src/application/jira/dto/jira-connect.dto.ts` | ⬜ |
| 5.3 | Create JiraTicketDto | `packages/bridge/src/application/jira/dto/jira-ticket.dto.ts` | ⬜ |
| 5.4 | Create JiraActivityDto | `packages/bridge/src/application/jira/dto/jira-ticket.dto.ts` | ⬜ |
| 5.5 | Create Jira controller | `packages/bridge/src/application/jira/jira.controller.ts` | ⬜ |
| 5.6 | Add connect endpoint | `packages/bridge/src/application/jira/jira.controller.ts` | ⬜ |
| 5.7 | Add getStatus endpoint | `packages/bridge/src/application/jira/jira.controller.ts` | ⬜ |
| 5.8 | Add getAssignedTickets endpoint | `packages/bridge/src/application/jira/jira.controller.ts` | ⬜ |
| 5.9 | Add getTicketDetails endpoint | `packages/bridge/src/application/jira/jira.controller.ts` | ⬜ |
| 5.10 | Add transitionTicket endpoint | `packages/bridge/src/application/jira/jira.controller.ts` | ⬜ |
| 5.11 | Add getDailyActivity endpoint | `packages/bridge/src/application/jira/jira.controller.ts` | ⬜ |

---

## Phase 4: JIRA Module Registration (Day 6)

**Goal**: Register JIRA module in NestJS application.

### Day 6: Module Integration

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 6.1 | Create JIRA module | `packages/bridge/src/application/jira/jira.module.ts` | ⬜ |
| 6.2 | Register JiraModule in AppModule | `packages/bridge/src/app.module.ts` | ⬜ |
| 6.3 | Verify module compiles | `packages/bridge/src/` | ⬜ |

---

## Phase 5: Web Dashboard (Days 7-8)

**Goal**: Create UI for users to connect JIRA and manage settings.

### Day 7: Web Components

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 7.1 | Create JiraCard React component | `apps/web/app/components/integrations/JiraCard.tsx` | ⬜ |
| 7.2 | Implement connection form UI | `apps/web/app/components/integrations/JiraCard.tsx` | ⬜ |
| 7.3 | Implement disconnect UI | `apps/web/app/components/integrations/JiraCard.tsx` | ⬜ |
| 7.4 | Add connection status display | `apps/web/app/components/integrations/JiraCard.tsx` | ⬜ |

### Day 8: Dashboard Integration

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 8.1 | Add JiraCard to dashboard | `apps/web/app/page.tsx` | ⬜ |
| 8.2 | Add connection handlers | `apps/web/app/page.tsx` | ⬜ |
| 8.3 | Add web API client methods | `apps/web/src/lib/api.ts` | ⬜ |
| 8.4 | Implement jiraApi.connect | `apps/web/src/lib/api.ts` | ⬜ |
| 8.5 | Implement jiraApi.getStatus | `apps/web/src/lib/api.ts` | ⬜ |
| 8.6 | Implement jiraApi.getAssignedTickets | `apps/web/src/lib/api.ts` | ⬜ |
| 8.7 | Implement jiraApi.getTicketDetails | `apps/web/src/lib/api.ts` | ⬜ |
| 8.8 | Implement jiraApi.transitionTicket | `apps/web/src/lib/api.ts` | ⬜ |
| 8.9 | Implement jiraApi.getDailyActivity | `apps/web/src/lib/api.ts` | ⬜ |

---

## Phase 6: Chat Integration (Days 9-11)

**Goal**: Add intent-based JIRA commands to chat adapters.

### Day 9: Intent Parser

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 9.1 | Create JiraIntentParser class | `packages/bridge/src/application/jira/intents/jira-intent-parser.ts` | ⬜ |
| 9.2 | Define intent patterns for list tickets | `packages/bridge/src/application/jira/intents/jira-intent-parser.ts` | ⬜ |
| 9.3 | Define intent patterns for get ticket details | `packages/bridge/src/application/jira/intents/jira-intent-parser.ts` | ⬜ |
| 9.4 | Define intent patterns for complete ticket | `packages/bridge/src/application/jira/intents/jira-intent-parser.ts` | ⬜ |
| 9.5 | Define intent patterns for add comment | `packages/bridge/src/application/jira/intents/jira-intent-parser.ts` | ⬜ |
| 9.6 | Define intent patterns for daily summary | `packages/bridge/src/application/jira/intents/jira-intent-parser.ts` | ⬜ |
| 9.7 | Define intent patterns for daily report | `packages/bridge/src/application/jira/intents/jira-intent-parser.ts` | ⬜ |
| 9.8 | Define intent patterns for search tickets | `packages/bridge/src/application/jira/intents/jira-intent-parser.ts` | ⬜ |

### Day 10: Message Router Integration

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 10.1 | Update MessageRouter constructor | `packages/bridge/src/application/adapters/message-router.service.ts` | ⬜ |
| 10.2 | Add handleJiraIntent method | `packages/bridge/src/application/adapters/message-router.service.ts` | ⬜ |
| 10.3 | Implement listTickets handler | `packages/bridge/src/application/adapters/message-router.service.ts` | ⬜ |
| 10.4 | Implement getTicketDetails handler | `packages/bridge/src/application/adapters/message-router.service.ts` | ⬜ |
| 10.5 | Implement completeTicket handler | `packages/bridge/src/application/adapters/message-router.service.ts` | ⬜ |
| 10.6 | Implement addComment handler | `packages/bridge/src/application/adapters/message-router.service.ts` | ⬜ |
| 10.7 | Implement getDailySummary handler | `packages/bridge/src/application/adapters/message-router.service.ts` | ⬜ |
| 10.8 | Implement generateDailyReport handler | `packages/bridge/src/application/adapters/message-router.service.ts` | ⬜ |
| 10.9 | Implement searchTickets handler | `packages/bridge/src/application/adapters/message-router.service.ts` | ⬜ |

### Day 11: Chat Adapter Commands

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 11.1 | Add Jira commands to help message | `packages/bridge/src/application/adapters/telegram.adapter.ts` | ⬜ |
| 11.2 | Update getHelpMessage method | `packages/bridge/src/application/adapters/telegram.adapter.ts` | ⬜ |
| 11.3 | Test intent parsing | `packages/bridge/test/jira/jira-intent-parser.spec.ts` | ⬜ |
| 11.4 | Test message router | `packages/bridge/test/adapters/message-router.service.spec.ts` | ⬜ |

---

## Phase 7: Testing & Documentation (Days 12-13)

**Goal**: Ensure all features work correctly and document usage.

### Day 12: Testing

| Step | Task | Status |
|------|------|--------|
| 12.1 | Test JIRA connection flow via dashboard | ⬜ |
| 12.2 | Test listing assigned tickets via chat | ⬜ |
| 12.3 | Test getting ticket details via chat | ⬜ |
| 12.4 | Test completing ticket via chat | ⬜ |
| 12.5 | Test getting daily summary via chat | ⬜ |
| 12.6 | Test adding comments to tickets | ⬜ |
| 12.7 | Verify token encryption works | ⬜ |
| 12.8 | Test all unit tests pass | ⬜ |
| 12.9 | Test error handling (invalid URL, bad API key) | ⬜ |

### Day 13: Documentation

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 13.1 | Update CLAUDE.md with JIRA section | `packages/bridge/CLAUDE.md` | ⬜ |
| 13.2 | Update README with JIRA features | `packages/bridge/README.md` | ⬜ |
| 13.3 | Document API token creation process | `packages/bridge/docs/JIRA_SETUP.md` | ⬜ |
| 13.4 | Create troubleshooting guide | `packages/bridge/docs/JIRA_TROUBLESHOOTING.md` | ⬜ |

---

## Phase 8: Deployment (Day 14)

**Goal**: Deploy and verify in environment.

### Day 14: Deployment

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 14.1 | Add JIRA_WEBHOOK_SECRET to .env | `packages/bridge/.env` | ⬜ |
| 14.2 | Build bridge package | `packages/bridge/` | ⬜ |
| 14.3 | Run migrations in staging | `packages/bridge/` | ⬜ |
| 14.4 | Test end-to-end in staging | `packages/bridge/` | ⬜ |
| 14.5 | Deploy to production | `packages/bridge/` | ⬜ |

---

## Success Criteria

### JIRA Integration is Complete When:

**Database & Foundation:**
☐ Database migration created and run
☐ User entity has Jira fields
☐ Token encryption utilities implemented
☐ Type definitions created and tested

**Service Layer:**
☐ JiraClient implemented with all methods
☐ JiraService with connect/disconnect
☐ getAssignedTickets works
☐ getTicketDetails works
☐ transitionTicket works
☐ getDailyActivity works

**API Layer:**
☐ All DTOs created
☐ All endpoints implemented
☐ All endpoints protected with JWT
☐ Module registered in app

**Web Dashboard:**
☐ JiraCard component created
☐ Connection form works
☐ Disconnect works
☐ API client methods implemented

**Chat Integration:**
☐ Intent parser handles all patterns
☐ Message router integrates Jira intents
☐ All handlers return user-friendly messages
☐ Commands added to help

**Testing:**
☐ Unit tests pass
☐ Integration tests pass
☐ Error handling verified
☐ Token encryption verified

**Documentation:**
☐ CLAUDE.md updated
☐ README updated
☐ Setup guide created
☐ Troubleshooting guide created

**Deployment:**
☐ Staging tested
☐ Production deployed
☐ Environment variables configured

---

## 📊 Total Progress

```
Phase 1: Database & Foundation     ░░░░░░░   0/11 steps
Phase 2: JIRA Service           ░░░░░░░   0/9 steps
Phase 3: Controller & DTOs       ░░░░░░░   0/11 steps
Phase 4: Module Integration       ░░░░░░░   0/3 steps
Phase 5: Web Dashboard           ░░░░░░░   0/9 steps
Phase 6: Chat Integration        ░░░░░░░   0/15 steps
Phase 7: Testing & Documentation  ░░░░░░░   0/13 steps
Phase 8: Deployment              ░░░░░░░   0/5 steps
────────────────────────────────────────────
Total                             ░░░░░░░   0/76 steps
```

---

## Future Enhancements

After core features are complete, consider adding:

1. **Webhooks** - Real-time notifications for new assignments
2. **Scheduler** - Morning standup and weekly reports
3. **OAuth 2.0** - Replace API tokens with OAuth
4. **Sprint Planning** - Integrate with Jira sprints
5. **Time Tracking** - Log work via chat
6. **Custom JQL** - Advanced filtering
7. **Attachments** - File upload support
8. **Board Views** - Kanban/scrum board in chat
9. **AI Insights** - Ticket priority suggestions

---

## Next Steps After Core JIRA

1. ✅ Review this plan and approve
2. ⏭️ Start with Phase 1: Database & Foundation
3. ⏭️ Implement Phase 2: JIRA Service
4. ⏭️ Implement Phase 3: Controller & DTOs
5. ⏭️ Implement Phase 4: Module Integration
6. ⏭️ Implement Phase 5: Web Dashboard
7. ⏭️ Implement Phase 6: Chat Integration
8. ⏭️ Implement Phase 7: Testing & Documentation
9. ⏭️ Implement Phase 8: Deployment
10. ⏭️ Test end-to-end
11. ⏭️ Deploy to production

---

**Ready to build Jira integration? Let's go!** 🚀
