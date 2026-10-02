# makefiles/controller.mk

.PHONY: rest trot crawl stand

##! Перевести робота в режим REST (отдых)
rest:
	$(call set-robot-mode,REST)

##! Перевести робота в режим TROT (бег рысью)
trot:
	$(call set-robot-mode,TROT)

##! Перевести робота в режим CRAWL (ползание)
crawl:
	$(call set-robot-mode,CRAWL)

##! Перевести робота в режим STAND (стойка)
stand:
	$(call set-robot-mode,STAND)
