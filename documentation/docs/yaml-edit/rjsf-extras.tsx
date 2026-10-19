import React from "react";
import { getDefaultRegistry } from "@rjsf/core";
import {
  ADDITIONAL_PROPERTY_FLAG,
  buttonId,
  canExpand,
  descriptionId,
  getSchemaType,
  getTemplate,
  getUiOptions,
  titleId,
  TranslatableString,
  type FieldTemplateProps,
  type BaseInputTemplateProps,
  type CustomValidator,
  type IconButtonProps,
  type ObjectFieldTemplateProps,
  type OptionalDataControlsTemplateProps,
  type UiSchema,
  type WrapIfAdditionalTemplateProps,
} from "@rjsf/utils";

const DefaultFieldTemplate = getDefaultRegistry().templates.FieldTemplate;
const DefaultBaseInputTemplate = getDefaultRegistry().templates.BaseInputTemplate;
const WindowOverrideKeysContext = React.createContext<string[]>([]);

function stringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

/** Default field template, minus the label that rjsf repeats above additional-property objects
 *  (the key input already shows the name). */
export function NoDuplicateLabelFieldTemplate(props: FieldTemplateProps) {
  const { schema, displayLabel } = props;
  const isAdditionalObject = ADDITIONAL_PROPERTY_FLAG in schema && getSchemaType(schema) === "object";
  return <DefaultFieldTemplate {...props} displayLabel={displayLabel && !isAdditionalObject} />;
}

/** Default input template, with numbers in plain text inputs: native number inputs change
 *  their value on scroll-wheel and spinner use. rjsf still converts the text to a number. */
export function TextNumberBaseInputTemplate(props: BaseInputTemplateProps) {
  const schemaType = getSchemaType(props.schema);
  if (schemaType !== "number" && schemaType !== "integer") {
    return <DefaultBaseInputTemplate {...props} />;
  }
  return <DefaultBaseInputTemplate {...props} options={{ ...props.options, inputType: "text" }} />;
}

/** Default rjsf template, with the key input label taken from `ui:options.keyLabel` when given. */
export function KeyLabelWrapIfAdditionalTemplate(props: WrapIfAdditionalTemplateProps) {
  const {
    id,
    classNames,
    style,
    disabled,
    label,
    onKeyRename,
    onKeyRenameBlur,
    onRemoveProperty,
    readonly,
    required,
    schema,
    hideError,
    rawErrors,
    children,
    uiSchema,
    registry,
  } = props;
  const { templates, translateString } = registry;
  const { RemoveButton } = templates.ButtonTemplates;
  const { keyLabel, keyOptions } = getUiOptions(uiSchema);
  const formContext = registry.formContext as { globalAttributes?: unknown };
  const globalAttributes = stringArray(formContext.globalAttributes);
  const usedOverrideKeys = React.useContext(WindowOverrideKeysContext);
  const availableAttributes = globalAttributes.filter(
    (attribute) => attribute === label || !usedOverrideKeys.includes(attribute),
  );
  const isAttributeKey = keyOptions === "globalAttributes";
  const keyLabelText =
    typeof keyLabel === "string" ? keyLabel : translateString(TranslatableString.KeyLabel, [label]);

  const classNamesList = ["form-group", classNames];
  if (!hideError && rawErrors && rawErrors.length > 0) {
    classNamesList.push("has-error has-danger");
  }
  const uiClassNames = classNamesList.join(" ").trim();

  if (!(ADDITIONAL_PROPERTY_FLAG in schema)) {
    return (
      <div className={uiClassNames} style={style}>
        {children}
      </div>
    );
  }
  return (
    <div className={uiClassNames} style={style}>
      <div className="additional-entry">
        <div className="additional-key">
          <label className="control-label" htmlFor={`${id}-key`}>
            {keyLabelText}
            {required && <span className="required">*</span>}
          </label>
          {isAttributeKey ? (
            <select
              className="form-control"
              id={`${id}-key`}
              value={globalAttributes.includes(label) ? label : ""}
              onChange={(event) => {
                if (event.currentTarget.value) {
                  onKeyRename(event.currentTarget.value);
                }
              }}
              disabled={disabled || readonly}
            >
              <option value="" disabled>
                Select an attribute
              </option>
              {availableAttributes.map((attribute) => (
                <option key={attribute} value={attribute}>
                  {attribute}
                </option>
              ))}
            </select>
          ) : (
            <input
              key={label}
              className="form-control"
              type="text"
              id={`${id}-key`}
              onBlur={onKeyRenameBlur}
              defaultValue={label}
            />
          )}
          <RemoveButton
            id={buttonId(id, "remove")}
            className="rjsf-object-property-remove"
            disabled={disabled || readonly}
            onClick={onRemoveProperty}
            uiSchema={uiSchema}
            registry={registry}
          />
        </div>
        {children}
      </div>
    </div>
  );
}

/** Text button whose caption comes from `ui:options[labelOption]`, falling back to `fallback`. */
function labelledButton(labelOption: "addLabel" | "removeLabel" | undefined, fallback: string, className: string) {
  return function LabelledButton(props: IconButtonProps) {
    const { uiSchema, registry: _registry, icon: _icon, iconType: _iconType, className: extra, ...rest } = props;
    const caption = labelOption ? getUiOptions(uiSchema)[labelOption] : undefined;
    return (
      <button type="button" className={`${className} ${extra ?? ""}`.trim()} {...rest}>
        {typeof caption === "string" ? caption : fallback}
      </button>
    );
  };
}

export const LabelledAddButton = labelledButton("addLabel", "Add new", "btn-text btn-text-add");
export const LabelledRemoveButton = labelledButton("removeLabel", "Delete", "btn-text btn-text-remove");
export const LabelledMoveUpButton = labelledButton(undefined, "Move up", "btn-text btn-text-move");
export const LabelledMoveDownButton = labelledButton(undefined, "Move down", "btn-text btn-text-move");

/** Renders rjsf's optional-data Add/Remove controls as a single checkbox labelled by `ui:options.optionalLabel`. */
export function CheckboxOptionalDataControlsTemplate(props: OptionalDataControlsTemplateProps) {
  const { id, label, onAddClick, onRemoveClick, uiSchema } = props;
  if (!onAddClick && !onRemoveClick) {
    return <em id={id}>{label}</em>;
  }
  const { optionalLabel } = getUiOptions(uiSchema);
  return (
    <label className="optional-toggle" htmlFor={id}>
      <input type="checkbox" id={id} checked={!!onRemoveClick} onChange={onRemoveClick ?? onAddClick} />
      {typeof optionalLabel === "string" ? optionalLabel : label}
    </label>
  );
}

/** Object template where the "add property" button is only shown once a checkbox is ticked. */
export function GatedExpandObjectFieldTemplate(props: ObjectFieldTemplateProps) {
  const { className, description, disabled, formData, fieldPathId, onAddProperty, properties, readonly, registry, required, schema, title, uiSchema } =
    props;
  const options = getUiOptions(uiSchema);
  const TitleFieldTemplate = getTemplate<"TitleFieldTemplate">("TitleFieldTemplate", registry, options);
  const DescriptionFieldTemplate = getTemplate<"DescriptionFieldTemplate">("DescriptionFieldTemplate", registry, options);
  const { AddButton } = registry.templates.ButtonTemplates;
  const formContext = registry.formContext as { globalAttributes?: unknown };
  const globalAttributes = stringArray(formContext.globalAttributes);
  const usedOverrideKeys = Object.keys(asRecord(formData) ?? {}).filter((key) =>
    globalAttributes.includes(key),
  );
  const existingOverrideKeys = Object.entries(schema.properties ?? {})
    .filter(
      ([, property]) =>
        typeof property === "object" && property !== null && ADDITIONAL_PROPERTY_FLAG in property,
    )
    .map(([key]) => key)
    .sort();
  const existingOverrideSignature = existingOverrideKeys.join("\0");
  const [showAdd, setShowAdd] = React.useState(existingOverrideKeys.length > 0);
  const toggleId = `${fieldPathId.$id}__expand-toggle`;
  const expandLabel = typeof options.expandLabel === "string" ? options.expandLabel : "Add entries";

  React.useEffect(() => {
    setShowAdd(existingOverrideSignature.length > 0);
  }, [existingOverrideSignature]);

  return (
    <WindowOverrideKeysContext.Provider value={usedOverrideKeys}>
      <fieldset className={className} id={fieldPathId.$id}>
        {title && (
          <TitleFieldTemplate id={titleId(fieldPathId)} title={title} required={required} schema={schema} uiSchema={uiSchema} registry={registry} />
        )}
        {description && (
          <DescriptionFieldTemplate id={descriptionId(fieldPathId)} description={description} schema={schema} uiSchema={uiSchema} registry={registry} />
        )}
        {properties.map((prop) => prop.content)}
        {canExpand(schema, uiSchema, formData) && (
          <div className="form-group">
            <label className="optional-toggle" htmlFor={toggleId}>
              <input type="checkbox" id={toggleId} checked={showAdd} onChange={(e) => setShowAdd(e.target.checked)} />
              {expandLabel}
            </label>
            {showAdd && (
              <AddButton
                id={buttonId(fieldPathId, "add")}
                className="rjsf-object-property-expand"
                onClick={onAddProperty}
                disabled={disabled || readonly}
                uiSchema={uiSchema}
                registry={registry}
              />
            )}
          </div>
        )}
      </fieldset>
    </WindowOverrideKeysContext.Provider>
  );
}

const optionalObject = (label: string): UiSchema => ({
  "ui:options": { enableOptionalDataFieldForType: ["object"], optionalLabel: label },
});

const windowFieldNames = new Set([
  "top_horizon",
  "bottom_horizon",
  "top_surface_shift",
  "bottom_surface_shift",
  "window_length",
  "error",
  "zone",
  "position",
]);

function asRecord(value: unknown): Record<string, unknown> | undefined {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
}

function errorHasSurface(error: unknown): boolean {
  const errorConfig = asRecord(error);
  const errorSurface = errorConfig?.error_surface;
  return typeof errorSurface === "string" && errorSurface.trim().length > 0;
}

function addValidationError(validation: unknown, message: string): void {
  const node = asRecord(validation);
  if (typeof node?.addError === "function") {
    node.addError(message);
  }
}

function validateErrorConfig(error: unknown, validation: unknown): void {
  const errorConfig = asRecord(error);
  if (!errorConfig || Object.keys(errorConfig).length === 0) {
    return;
  }

  if (typeof errorConfig.error_surface === "string" && !errorConfig.error_surface.trim()) {
    addValidationError(validation, "error_surface must not be blank.");
  }
  const hasValue = errorConfig.value !== undefined && errorConfig.value !== null;
  const hasSurface = errorHasSurface(errorConfig);
  const hasType = errorConfig.type !== undefined && errorConfig.type !== null;
  if (!hasType && !hasValue && !hasSurface && (errorConfig.minimum == null || errorConfig.minimum === 0)) {
    return;
  }

  if (hasValue === hasSurface) {
    addValidationError(validation, "Set exactly one of value or error_surface.");
  }
  if (typeof errorConfig.value === "number" && errorConfig.value < 0) {
    addValidationError(validation, "Error value must be non-negative.");
  }
  if (typeof errorConfig.minimum === "number" && errorConfig.minimum < 0) {
    addValidationError(validation, "Error minimum must be non-negative.");
  }
}

export const validateIntervalConfig: CustomValidator = (formData, errors) => {
  const root = asRecord(formData);
  const globalConfig = asRecord(root?.global);
  const errorState = asRecord(errors);
  const globalErrorState = asRecord(errorState?.global);
  const rootCubes = root?.cubes;
  const cubes: unknown[] = Array.isArray(rootCubes) ? rootCubes : [];
  const cubesErrorState = asRecord(errorState?.cubes);
  const globalAttributes = new Set(stringArray(globalConfig?.attributes));
  const errorPath = globalConfig?.error_path;

  validateErrorConfig(globalConfig?.error, globalErrorState?.error);

  let usesErrorSurface = errorHasSurface(globalConfig?.error);
  const seenPrefixes = new Set<string>();
  cubes.forEach((cubeData, cubeIndex) => {
    const cube = asRecord(cubeData);
    const cubeErrorState = asRecord(cubesErrorState?.[cubeIndex]);
    if (typeof cube?.cube_prefix === "string") {
      // A trailing '--' does not change which cubes a prefix matches
      const prefix = cube.cube_prefix.replace(/--$/, "");
      if (seenPrefixes.has(prefix)) {
        addValidationError(
          cubeErrorState?.cube_prefix ?? cubeErrorState,
          `cube_prefix '${cube.cube_prefix}' is given more than once.`,
        );
      }
      seenPrefixes.add(prefix);
    }
    validateErrorConfig(cube?.error, cubeErrorState?.error);
    usesErrorSurface ||= errorHasSurface(cube?.error);

    const windows = asRecord(cube?.windows);
    for (const [windowName, windowData] of Object.entries(windows ?? {})) {
      const window = asRecord(windowData);
      const windowErrorState = asRecord(cubeErrorState?.windows)?.[windowName];

      const invalidOverrides = Object.keys(window ?? {}).filter(
        (key) => !windowFieldNames.has(key) && !globalAttributes.has(key),
      );
      if (invalidOverrides.length > 0) {
        addValidationError(
          windowErrorState,
          `Overrides ${invalidOverrides.join(", ")} must be listed in global.attributes.`,
        );
      }

      if (window?.bottom_horizon == null && window?.window_length == null) {
        addValidationError(
          windowErrorState,
          "Set either bottom_horizon or window_length for this window.",
        );
      }
      validateErrorConfig(window?.error, asRecord(windowErrorState)?.error);
      usesErrorSurface ||= errorHasSurface(window?.error);
    }
  });

  if (usesErrorSurface && !(typeof errorPath === "string" && errorPath.trim())) {
    // RJSF only creates error nodes for keys present in the data
    addValidationError(
      globalErrorState?.error_path ?? globalErrorState ?? errorState,
      "error_path is required when an error_surface is set at global, cube, or window level.",
    );
  }
  return errors;
};

/** Labels and opt-in controls for the interval definition form. */
export const intervalUiSchema: UiSchema = {
  cubes: {
    "ui:options": { addLabel: "Add cube" },
    items: {
      "ui:options": { removeLabel: "Delete cube" },
      error: optionalObject("Specify an observation error for this cube"),
      windows: {
        "ui:options": { addLabel: "Add window" },
        additionalProperties: {
          "ui:title": "",
          "ui:ObjectFieldTemplate": GatedExpandObjectFieldTemplate,
          "ui:options": {
            keyLabel: "Window name:",
            removeLabel: "Delete window",
            expandLabel: "Add per-attribute overrides",
            addLabel: "Add attribute override",
          },
          error: optionalObject("Specify an observation error for this window"),
          additionalProperties: {
            "ui:title": "",
            "ui:options": {
              keyLabel: "Applies to attribute:",
              keyOptions: "globalAttributes",
              removeLabel: "Delete override",
            },
          },
        },
      },
    },
  },
};
