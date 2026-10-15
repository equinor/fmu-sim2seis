import { type RJSFSchema } from "@rjsf/utils";
import sim2seisJsonSchema from "./fmu-sim2seis-schema.json";
import intervalJsonSchema from "./fmu-sim2seis-intervals-schema.json";

// @ts-ignore
export const sim2seisSchema: RJSFSchema = sim2seisJsonSchema;
// @ts-ignore
export const intervalSchema: RJSFSchema = intervalJsonSchema;
