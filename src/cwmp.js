const { XMLParser, XMLBuilder } = require('fast-xml-parser');
const { nanoid } = require('nanoid');

const xmlParser = new XMLParser({
  ignoreAttributes: false,
  attributeNamePrefix: '@_',
  removeNSPrefix: false,
  allowBooleanAttributes: true,
  parseTagValue: true,
  parseAttributeValue: true,
});

const xmlBuilder = new XMLBuilder({
  ignoreAttributes: false,
  attributeNamePrefix: '@_',
  suppressEmptyNode: true,
  format: true,
});

function parseSoap(xmlString) {
  try {
    const json = xmlParser.parse(xmlString);
    return json;
  } catch (e) {
    const error = new Error('Failed to parse SOAP XML');
    error.cause = e;
    throw error;
  }
}

function getCwmpMethodName(envelope) {
  const body = envelope?.['s:Envelope']?.['s:Body'] || envelope?.Envelope?.Body || envelope?.['soap-env:Envelope']?.['soap-env:Body'];
  if (!body) return null;
  const keys = Object.keys(body);
  if (keys.length === 0) return null;
  // Skip Fault and headers
  const methodKey = keys.find((k) => !['Fault'].includes(k));
  return methodKey || null;
}

function buildSoapEnvelope({ header = {}, body }) {
  const envelope = {
    'soap-env:Envelope': {
      '@_xmlns:soap-env': 'http://schemas.xmlsoap.org/soap/envelope/',
      '@_xmlns:soap-enc': 'http://schemas.xmlsoap.org/soap/encoding/',
      '@_xmlns:xsd': 'http://www.w3.org/2001/XMLSchema',
      '@_xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
      '@_xmlns:cwmp': 'urn:dslforum-org:cwmp-1-0',
      'soap-env:Header': header,
      'soap-env:Body': body,
    },
  };
  return xmlBuilder.build(envelope);
}

function buildInformResponse({ maxEnvelopes = 1, idHeader }) {
  const header = {};
  if (idHeader) {
    header['cwmp:ID'] = { '@_soap-env:mustUnderstand': 1, '#text': idHeader };
  }
  const body = {
    'cwmp:InformResponse': {
      'MaxEnvelopes': maxEnvelopes,
    },
  };
  return buildSoapEnvelope({ header, body });
}

function extractInformData(envelope) {
  const body = envelope?.['s:Envelope']?.['s:Body']
    || envelope?.Envelope?.Body
    || envelope?.['soap-env:Envelope']?.['soap-env:Body'];
  if (!body) return null;
  const inform = body['cwmp:Inform'] || body.Inform || body['cwmp-1-0:Inform'];
  if (!inform) return null;
  const deviceId = inform?.DeviceId || inform?.DeviceID;
  const oui = deviceId?.OUI || deviceId?.Oui || deviceId?.oui || null;
  const serialNumber = deviceId?.SerialNumber || deviceId?.Serialnumber || null;
  const productClass = deviceId?.ProductClass || deviceId?.Productclass || null;
  const manufacturer = deviceId?.Manufacturer || null;

  // ConnectionRequestURL often inside ParameterList items
  let connectionRequestURL = null;
  const parameterList = inform?.ParameterList?.ParameterValueStruct || inform?.ParameterList || [];
  const paramsArray = Array.isArray(parameterList) ? parameterList : [parameterList];
  for (const p of paramsArray) {
    const name = p?.Name || p?.name;
    const value = p?.Value || p?.Value?.['#text'] || p?.value;
    if (typeof name === 'string' && name.endsWith('ManagementServer.ConnectionRequestURL')) {
      connectionRequestURL = typeof value === 'object' ? value?.['#text'] : value;
    }
  }

  return {
    manufacturer,
    oui,
    productClass,
    serialNumber,
    connectionRequestURL,
  };
}

function buildGetParameterValues({ parameterNames, id }) {
  const idHeader = id || nanoid();
  const header = {
    'cwmp:ID': { '@_soap-env:mustUnderstand': 1, '#text': idHeader },
  };
  const namesArray = Array.isArray(parameterNames) ? parameterNames : [parameterNames];
  const body = {
    'cwmp:GetParameterValues': {
      'ParameterNames': {
        '@_soap-enc:arrayType': `xsd:string[${namesArray.length}]`,
        'string': namesArray,
      },
    },
  };
  return { xml: buildSoapEnvelope({ header, body }), id: idHeader };
}

function buildReboot({ commandKey = '', id }) {
  const idHeader = id || nanoid();
  const header = {
    'cwmp:ID': { '@_soap-env:mustUnderstand': 1, '#text': idHeader },
  };
  const body = {
    'cwmp:Reboot': {
      'CommandKey': commandKey,
    },
  };
  return { xml: buildSoapEnvelope({ header, body }), id: idHeader };
}

module.exports = {
  parseSoap,
  getCwmpMethodName,
  buildInformResponse,
  extractInformData,
  buildGetParameterValues,
  buildReboot,
};
