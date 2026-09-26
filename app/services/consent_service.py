"""ConsentService: explicit, recorded permission to clone a person's voice."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.status import Status
from app.exceptions import ConsentError, service_error
from app.models import VoiceConsent
from app.utils.database import read_session, serialize
from app.utils.logger import logger
from app.utils.time import utcnow

CONSENT_STATEMENT = (
    "I confirm that {speaker} is the person heard in these recordings, that they have given "
    "explicit permission for their voice to be cloned with VoxLabs, and that the cloned voice "
    "will not be used to deceive, impersonate or harm anyone."
)


class ConsentService:
    def statement_for(self, speaker_name: str) -> str:
        return CONSENT_STATEMENT.format(speaker=speaker_name or "the speaker")

    def validate(self, consent: dict | None) -> dict:
        """Raise ConsentError unless consent was explicitly confirmed and attributed."""
        try:
            consent = consent or {}
            if consent.get("confirmed") is not True:
                raise ConsentError("Voice cloning requires explicit consent from the speaker", field="consent")
            granted_by = (consent.get("granted_by") or "").strip()
            speaker = (consent.get("speaker_name") or "").strip()
            if not granted_by:
                raise ConsentError("Enter who is granting consent", field="granted_by")
            if not speaker:
                raise ConsentError("Enter the name of the person whose voice is cloned", field="speaker_name")
            return {
                "granted_by": granted_by,
                "speaker_name": speaker,
                "statement": (consent.get("statement") or "").strip() or self.statement_for(speaker),
            }
        except Exception as exc:
            raise service_error(exc, "consent_service.validate")

    def record(self, session: Session, voices_id: int, consent: dict) -> VoiceConsent:
        data = self.validate(consent)
        row = VoiceConsent(voices_id=voices_id, granted_at=utcnow(), status=Status.ACTIVE.code, **data)
        session.add(row)
        session.flush()
        logger.info(f"Consent recorded for voice {voices_id}")
        return row

    def has_active(self, session: Session, voices_id: int) -> bool:
        return (
            session.scalar(
                select(VoiceConsent.voice_consents_id).where(
                    VoiceConsent.voices_id == voices_id, VoiceConsent.status == Status.ACTIVE.code
                )
            )
            is not None
        )

    def require_active(self, session: Session, voices_id: int) -> None:
        if not self.has_active(session, voices_id):
            raise ConsentError("This voice has no active consent record", field="voices_id")

    def revoke(self, session: Session, voices_id: int) -> int:
        rows = session.scalars(
            select(VoiceConsent).where(VoiceConsent.voices_id == voices_id, VoiceConsent.status == Status.ACTIVE.code)
        ).all()
        for row in rows:
            row.status = Status.INACTIVE.code
            row.revoked_at = utcnow()
        if rows:
            logger.info(f"Consent revoked for voice {voices_id}")
        return len(rows)

    def history(self, voices_id: int) -> list[dict]:
        try:
            with read_session() as session:
                rows = session.scalars(
                    select(VoiceConsent).where(VoiceConsent.voices_id == voices_id).order_by(VoiceConsent.created_at)
                )
                return [serialize(r) for r in rows]
        except Exception as exc:
            raise service_error(exc, "consent_service.history")


consent_service = ConsentService()
