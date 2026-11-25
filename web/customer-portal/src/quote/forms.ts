import type { ComponentType } from "react";
import type { QuoteRequest } from "../api/policyApi";
import type { LineCode } from "../model/Policy";
import { MotorQuoteForm } from "./forms/MotorQuoteForm";
import { HomeBuildingsQuoteForm } from "./forms/HomeBuildingsQuoteForm";
import { ContentsQuoteForm } from "./forms/ContentsQuoteForm";
import { TravelQuoteForm } from "./forms/TravelQuoteForm";
import { PetQuoteForm } from "./forms/PetQuoteForm";
import { LandlordQuoteForm } from "./forms/LandlordQuoteForm";
import { MarineCargoQuoteForm } from "./forms/MarineCargoQuoteForm";
import { CommercialPropertyQuoteForm } from "./forms/CommercialPropertyQuoteForm";
import { PublicLiabilityQuoteForm } from "./forms/PublicLiabilityQuoteForm";
import { ProfessionalIndemnityQuoteForm } from "./forms/ProfessionalIndemnityQuoteForm";
import { CyberQuoteForm } from "./forms/CyberQuoteForm";
import { GadgetQuoteForm } from "./forms/GadgetQuoteForm";

export type QuoteFormProps = { onSubmit: (req: QuoteRequest) => void };

export const FORMS: Record<LineCode, ComponentType<QuoteFormProps>> = {
  MTR: MotorQuoteForm,
  HOM: HomeBuildingsQuoteForm,
  CNT: ContentsQuoteForm,
  TRV: TravelQuoteForm,
  PET: PetQuoteForm,
  LLD: LandlordQuoteForm,
  MAR: MarineCargoQuoteForm,
  CPR: CommercialPropertyQuoteForm,
  PLB: PublicLiabilityQuoteForm,
  PIN: ProfessionalIndemnityQuoteForm,
  CYB: CyberQuoteForm,
  GDG: GadgetQuoteForm,
};
